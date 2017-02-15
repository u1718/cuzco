from django.shortcuts import render, get_object_or_404
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

from bokeh.models import ColumnDataSource, DataRange1d, Select
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
        if 'username' in self.kwargs:
            username = self.request.user.username
            cities_by_name = City.objects.filter(user_name=username).order_by('name')
        else:
            cities_by_name = City.objects.order_by('name')
            
        for c in cities_by_name:
            o = c.owm_set.latest('req_date')

            sr, st = calc_ss(
                d=o.req_date.day, m=o.req_date.month, y=o.req_date.year, h=o.req_date.hour,
                lat=o.coord_lat, lon=o.coord_lon)
            
            fs = []
            # select the tools we want
            tempd = []
            windd = []
            presd = []
            humid = []
            timed = []
            #yr1 = Range1d(start=-30, end=30)
            for f in o.owmforecast_set.order_by('id'):
                fd = json.loads(f.forecast_text.replace("'",'"'))
                fd['main']['temp'] = "{0:.1f}".format(float(fd['main']['temp']) - 273.15)
                tempd.append(fd['main']['temp'])
                fd['main']['pressure'] = "{0:.2f}".format(float(fd['main']['pressure']))
                presd.append(fd['main']['pressure'])
                fd['main']['humidity'] = "{0:.0f}".format(float(fd['main']['humidity']))
                humid.append(fd['main']['humidity'])
                fd['wind']['speed'] = "{0:.1f}".format(float(fd['wind']['speed']))
                windd.append(fd['wind']['speed'])
                fd['dt'] = datetime.datetime.fromtimestamp(int(fd['dt']))
                timed.append(fd['dt']) #.strftime("%I:%M"))
                fs.append(fd)

            script, div = {}, {}
            # create a new plot with a title and axis labels
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            # add a line renderer with legend and line thickness
            p.line(timed, tempd, legend="Temperature, °C", line_width=2)
            script['temp'], div['temp'] = components(p)
            
            # create a new plot with a title and axis labels
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            # add a line renderer with legend and line thickness
            p.line(timed, humid, legend="Humidity, %", line_width=2)
            script['humi'], div['humi'] = components(p)

            # create a new plot with a title and axis labels
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            # add a line renderer with legend and line thickness
            p.line(timed, windd, legend="Wind, m/s", line_width=2)
            script['wind'], div['wind'] = components(p)
            
            # create a new plot with a title and axis labels
            p = figure(
                width=600, height=350, 
                tools="",
                toolbar_location=None,
                title='Weather and forecasts in {}, {}'.format(o.name, o.country),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
                )
            # add a line renderer with legend and line thickness
            p.line(timed, presd, legend="Pressure, hpa", line_width=2)
            script['pres'], div['pres'] = components(p)
            
            city_list.append({'city': c, 'owm': o,
                              'sunrise':sr, 'sunset': st,
                              'forecasts': fs[:9],
                              'script': script, 'div': div})

        return city_list

def gr1(request):
    plot = figure()
    plot.circle([1,2], [3,4])

    html = file_html(plot, CDN, "my plot")
    return HttpResponse(html)


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
