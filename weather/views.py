from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import generic
from django.utils import timezone
from django.views.generic.dates import TodayArchiveView, DayArchiveView

import datetime

import requests
import json

from .models import City, OWM, OWMForecast
from .sbcalendar import SideBarCalendar
from .forms import CityModelForm

import ephem

import pandas as pd
import numpy as np

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html, components

from bokeh.models import ColumnDataSource, DataRange1d, Select, Range1d, LinearAxis
from bokeh.layouts import row, column

class CitiesView(generic.ListView): #(LoginRequiredMixin, generic.ListView):
    #login_url = ''
    #redirect_field_name = ''
    template_name = 'weather/city_list.html'
    context_object_name = 'city_list' #== object_list
    paginate_by = 20

    def get_queryset(self):
        """Return requested cities."""
        city_list = list()
        if 'username' in self.kwargs and \
           self.kwargs['username'] == self.request.user.username:

            username = self.request.user.username
            cities = \
              get_list_or_404(City, user_name=username)#.order_by('name')
        else:
            cities = get_list_or_404(City)#.order_by('name')

        for c in sorted(cities, key=lambda x: x.name):
            o = c.owm_set.latest('req_date')

            sr, st = calc_ss(
                d=o.req_date.day, m=o.req_date.month, y=o.req_date.year, h=o.req_date.hour,
                lat=o.coord_lat, lon=o.coord_lon)
            
            fs = []
            tempd = []
            tempnd = []
            tempxd = []
            windd = []
            presd = []
            pressd = []
            presgd = []
            humid = []
            precd = []
            timed = []
            for f in o.owmforecast_set.order_by('id'):
                fd = json.loads(f.forecast_text.replace("'",'"'))

                tempd.append(float(fd['main']['temp']) - 273.15)
                fd['main']['temp'] = "{0:.1f}".format(tempd[-1])
                tempnd.append(float(fd['main']['temp_min']) - 273.15)
                fd['main']['temp_min'] = "{0:.1f}".format(tempnd[-1])
                tempxd.append(float(fd['main']['temp_max']) - 273.15)
                fd['main']['temp_max'] = "{0:.1f}".format(tempxd[-1])

                presd.append(float(fd['main']['pressure']))
                pressd.append(float(fd['main']['sea_level']))
                presgd.append(float(fd['main']['grnd_level']))
                humid.append(float(fd['main']['humidity']))
                windd.append(float(fd['wind']['speed']))
                
                if 'snow' in fd and '3h' in fd['snow']:
                    precd.append(float(fd['snow']['3h']))
                elif 'rain' in fd and '3h' in fd['rain']:
                    precd.append(float(fd['rain']['3h']))
                else:
                    precd.append(0)

                fd['dt'] = datetime.datetime.fromtimestamp(int(fd['dt']))
                timed.append(fd['dt'])
                
                fs.append(fd)

            script, div = {}, {}
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            p.extra_y_ranges = {"prec": Range1d(start=0, end=max([0]+precd))}
            p.add_layout(LinearAxis(y_range_name="prec"), 'right')
            x=np.append(timed, timed[::-1])
            y=np.append(tempnd, tempxd[::-1])
            p.patch(x, y, color='#7570B3', fill_alpha=0.2)
            p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm", color="grey", y_range_name="prec")
            p.line(timed, tempd, legend="Temperature, °C", line_width=2, color='blue')

            script['temp'], div['temp'] = components(p)
            
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            p.line(timed, humid, legend="Humidity, %", line_width=2)
            script['humi'], div['humi'] = components(p)

            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            p.line(timed, windd, legend="Wind, m/s", line_width=2)
            script['wind'], div['wind'] = components(p)
            
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            ls = '#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d #ffad33 #ffa31a #ff9900'.split()
            us = '#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 #85adad #75a3a3 #669999'.split()
            us = us[::-1]
            x = np.append(timed, timed[::-1])
            prs = 850
            for color in us + ls:
                y = [prs]*len(timed) + [prs+13.33]*len(timed)
                prs+=13.33
                p.patch(x, y, color=color, fill_alpha=0.2)

            p.line(timed, presd, legend="Pressure, hpa", line_width=4)
            #p.line(timed, pressd, legend="Pressure(sea level), hpa", line_width=3, color='grey')
            #p.line(timed, presgd, legend="Pressure(ground level), hpa", line_width=2, color='green')

            script['pres'], div['pres'] = components(p)
            
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm")
            script['prec'], div['prec'] = components(p)
            
            city_list.append({'city': c, 'owm': o,
                              'sunrise':sr, 'sunset': st,
                              'forecasts': fs[:9],
                              'script': script, 'div': div})

        return city_list

def gr(request, owm_id):
    o = OWM.objects.get(id=owm_id)
    fs = []
    dt = []
    for f in o.owmforecast_set.order_by('id')[:9]:
        fd = json.loads(f.forecast_text.replace("'",'"'))
        fs.append(float(fd['main']['temp']) - 273.15)
        dt.append(datetime.datetime.utcfromtimestamp(int(fd['dt'])).strftime("%I:%M"))

    fig = Figure()
    ax = fig.add_subplot(111)

    data_df = pd.DataFrame(fs, index=dt, columns=['temperature °C'])
    data_df.plot(ax=ax)

    canvas = FigureCanvas(fig)
    response = HttpResponse( content_type = 'image/png')
    canvas.print_png(response)

    return response

def calc_ss(d, m, y, h, lat, lon):
    o = ephem.Observer()
    o.lat, o.long, o.date = lat, lon, datetime.datetime(y, m, d, h)
    sun = ephem.Sun(o)
    
    sr = ephem.Date(o.next_rising(sun, start=o.date))
    st = ephem.Date(o.next_setting(sun, start=o.date))
    if sr > st:
        sr = ephem.Date(o.previous_rising(sun, start=o.date))
    elif o.date > st:
        sr = ephem.Date(o.previous_rising(sun, start=o.date))
        st = ephem.Date(o.previous_setting(sun, start=o.date))
        
    return sr, st
            
class CityView(generic.ListView): #(LoginRequiredMixin, generic.ListView):
    template_name = 'weather/city_detail.html'
    context_object_name = 'owm_list'
    paginate_by = 20
    
    def get_queryset(self):
        self.city = get_object_or_404(City, id=self.kwargs['pk'])
        return self.city.owm_set.order_by('-id')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CityView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['city'] = self.city
        return context
    
@login_required    
def city_update(request, city_id):
    city = get_object_or_404(City, pk=city_id)
    
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = CityModelForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            city.name = form.cleaned_data['name'] #request.POST['name']
            city.ds_owm = form.cleaned_data['ds_owm'] #request.POST['ds_owm']
            user_name = request.user.username
            city.user_name = user_name
            city.save()
            # redirect to a new URL:
            #return HttpResponseRedirect('weather:city_detail')
            # Always return an HttpResponseRedirect after successfully dealing
            # with POST data. This prevents data from being posted twice if a
            # user hits the Back button.
            return HttpResponseRedirect(reverse('weather:city_view', args=(city.id,)))

    # if a GET (or any other method) we'll create a blank form
    else:
        form = CityModelForm(initial={'name': city.name, 'ds_owm': city.ds_owm})

    return render(request, 'weather/city_detail_form.html', {'form': form, 'city': city})

class OWMView(generic.ListView): #(LoginRequiredMixin, generic.ListView):
    template_name = 'weather/owm_detail.html'
    context_object_name = 'owmforecast_list'
    
    def get_queryset(self):
        self.owm = get_object_or_404(OWM, id=self.kwargs['pk'])
        return self.owm.owmforecast_set.all()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OWMView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['owm'] = self.owm
        return context
        


def cron(request):
    username = request.GET['username']
    password = request.GET['password']
    user = authenticate(username=username, password=password)

    context = dict()
    
    if user is not None:
        login(request, user)
        
        c = City.objects.filter(turn=True).first()
        if c is None:
            City.objects.all().update(turn=True)
            c = City.objects.first()

        c.turn = False
        c.save()
            
        context.update({'c': {'name': c.name, 'ds_owm': c.ds_owm}})
        
        #ex: url_= 'http://api.openweathermap.org/data/2.5/forecast/city?id=498698&APPID=775670b8133c08911511535c6b1dfbdf'
        #ex: url = 'http://api.openweathermap.org/data/2.5/forecast/city'
        #ex: params = {
        #ex:     'id':r'498698',
        #ex:     'appid':r'775670b8133c08911511535c6b1dfbdf'
        #ex: }
        #ex: resp = requests.get(url_)
        #ex: resp = requests.get(url, params = params)
            
        if not False:
            resp = requests.get(c.ds_owm)

        else:
            with open('./owm.data.{}'.format(c.name)) as f:
                r = f.read()

            class Resp:
                def __init__(self, t):
                    self.text = t

            resp = Resp(r)

        if resp is not None:

            pj = json.loads(resp.text)

            if pj['cod'] == '0':
                context.update({
                    'fail': '',
                    'error': pj['message']
                })
                owm = OWM()

                owm.message = pj['message']

                owm.city = c
                owm.req_date = timezone.now()

                owm.save()

            else:
                context.update({
                    'ok': '',
                    'root': pj.keys(),
                    'city': pj['city'],
                    'list': pj['list'],
                })

                owm = OWM()

                owm.iden = pj['city']['id']
                owm.name = pj['city']['name']
                owm.coord_lon = pj['city']['coord']['lon']
                owm.coord_lat = pj['city']['coord']['lat']
                owm.country = pj['city']['country']
                owm.population = pj['city']['population']
                owm.sys_population = pj['city']['sys']['population']

                owm.cod = pj['cod']
                owm.message = pj['message']
                owm.cnt = pj['cnt']

                owm.city = c
                owm.req_date = timezone.now()

                owm.save()

                for fcs in pj['list']:
                    owm_forecast = OWMForecast()

                    owm_forecast.owm = owm
                    owm_forecast.forecast_text = fcs
                    owm_forecast.save()

        else:
            context.update({
                'fail': '',
                'error': c.name + ' req fail'
            })

            owm = OWM()

            owm.message = c.ds_owm + ': no response'

            owm.city = c
            owm.req_date = timezone.now()

            owm.save()

        logout(request)
        
    else:
        context.update({
            'fail': '',
            'error': 'auth fail'
        })
        
    return render(request, 'weather/cron.html', context)

class OWMTodayArchiveView(TodayArchiveView): #(LoginRequiredMixin, TodayArchiveView):
    #queryset = OWM.objects.all()
    #date_field = "req_date"
    allow_future = True
    make_object_list = True
    allow_empty = True
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        req_date = timezone.now()

        kwargs['req_date'] = timezone.now()
        kwargs['calendar'] = SideBarCalendar('weather:archive_day', req_date).formatmonth()

        return super(OWMTodayArchiveView, self).get_context_data(**kwargs)


class OWMDayArchiveView(DayArchiveView): #(LoginRequiredMixin, DayArchiveView):
    queryset = OWM.objects.all()
    date_field = "req_date"
    allow_future = True
    make_object_list = True
    allow_empty = True
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        req_date = timezone.datetime(int(self.get_year()), int(self.get_month()), int(self.get_day()))
        kwargs['req_date'] = req_date
        kwargs['calendar'] = SideBarCalendar('weather:archive_day', req_date).formatmonth()

        return super(OWMDayArchiveView, self).get_context_data(**kwargs)
