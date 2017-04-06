from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import generic
from django.utils import timezone
from django.views.generic.dates import TodayArchiveView, DayArchiveView
from django.db import connection

import datetime
from dateutil import parser
from itertools import chain
import requests
import json
import time
import pytz

from .models import City, OWM, OWMForecast, Yahoo, YahooForecast, RequestArchive
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
        city_list = list()
        if 'username' in self.kwargs and \
           self.kwargs['username'] == self.request.user.username:

            username = self.request.user.username
            cities = get_list_or_404(City, user_name=username)
        else:
            cities = get_list_or_404(City)

        for c in sorted(cities, key=lambda x: x.name):
            owmd = draw_owm(c)
            yahd = draw_yah(c)
            city_list.append({'city': c,
                              'owm': {'owm': owmd['o'],
                                      'sunrise':owmd['sr'], 'sunset': owmd['st'],
                                      'forecasts': owmd['fcs'][:9],
                                      'script': owmd['script'], 'div': owmd['div']},
                              'yahoo': {'yahoo': yahd['y'], 'yah':yahd['yy'],
                                        'forecasts': yahd['fcs'][:9],
                                        'script': yahd['script'], 'div': yahd['div']}})

        #import pdb; pdb.set_trace()
        return city_list
    
def draw_owm(c):
    o = c.owm_set.latest('req_date')
    
    sr, st = calc_ss(
        d=o.req_date.day, m=o.req_date.month, y=o.req_date.year, h=o.req_date.hour,
        lat=o.coord_lat, lon=o.coord_lon)

    sr = timezone.localtime(timezone.make_aware(sr.datetime()), timezone=pytz.timezone('Europe/Moscow'))
    st = timezone.localtime(timezone.make_aware(st.datetime()), timezone=pytz.timezone('Europe/Moscow'))

    fcs = []
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

        windd.append(float(fd['wind']['speed']))
        presd.append(float(fd['main']['pressure']))
        pressd.append(float(fd['main']['sea_level']))
        presgd.append(float(fd['main']['grnd_level']))
        humid.append(float(fd['main']['humidity']))

        if 'snow' in fd and '3h' in fd['snow']:
            precd.append(float(fd['snow']['3h']))
        elif 'rain' in fd and '3h' in fd['rain']:
            precd.append(float(fd['rain']['3h']))
        else:
            precd.append(0)

        fd['dt'] = datetime.datetime.fromtimestamp(int(fd['dt']), pytz.timezone('UTC'))
        #import pdb; pdb.set_trace()
        fd['dt'] = fd['dt'].astimezone(pytz.timezone('Europe/Moscow'))
        #import pdb; pdb.set_trace()
        timed.append(fd['dt'])

        fcs.append(fd)

    script, div = {}, {}

    p = figure(
        width=600, height=350, 
        tools="",
        toolbar_location=None,
        title='Weather and forecasts in {}, {}'.format(o.name, o.country),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.sizing_mode = 'scale_width'
    p.extra_y_ranges = {"prec": Range1d(start=0, end=max([0]+precd))}
    p.add_layout(LinearAxis(y_range_name="prec"), 'right')
    x=np.append(timed, timed[::-1])
    y=np.append(tempnd, tempxd[::-1])
    p.patch(x, y, color='#7570B3', fill_alpha=0.2)
    p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm", color="grey", y_range_name="prec")
    p.line(timed, tempd, legend="Temperature, °C", line_width=3, color='blue')

    script['temp'], div['temp'] = components(p)

    p = figure(
        width=600, height=350, 
        tools="",
        toolbar_location=None,
        title='Weather and forecasts in {}, {}'.format(o.name, o.country),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.sizing_mode = 'scale_width'
    us='#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d ' +\
       '#ffad33 #ffa31a #ff9900 #e68a00 #cc7a00 #b36b00 #995c00 ' +\
       '#804d00 #663d00 #4d2e00 #331f00 #1a0f00'
    ls='#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 ' +\
       '#85adad #75a3a3 #669999 #5c8a8a #527a7a #476b6b #3d5c5c ' +\
       '#334d4d #293d3d #1f2e2e #141f1f #0a0f0f'
    us = us.split()
    us = us[:5]
    us = us[::-1]
    ls = ls.split()
    ls = ls[:5]
    x = np.append(timed, timed[::-1])
    unp=70
    lnp=40
    up=100
    lp=0
    y = [lp + i * (lnp - lp) / len(ls) for i in range(0, len(ls) + 1)] +\
        [unp + i * (up - unp) / len(us) for i in range(0, len(us) + 1)]
    i = 0
    #import pdb; pdb.set_trace()
    for color in us + ['#ffffff'] + ls:
        p.patch(x, [y[i]]*len(timed) + [y[i+1]]*len(timed) , color=color)#, fill_alpha=0.2)
        i += 1

    for i in range(len(timed)):
        p.line([x[i],x[i]], [y[0],y[-1]], color='grey', line_width=.3) 

    p.line(timed, humid, legend="Humidity, %", line_width=3)
    script['humi'], div['humi'] = components(p)

    p = figure(
        width=600, height=350, 
        tools="",
        toolbar_location=None,
        title='Weather and forecasts in {}, {}'.format(o.name, o.country),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.sizing_mode = 'scale_width'
    p.line(timed, windd, legend="Wind, m/s", line_width=3)
    script['wind'], div['wind'] = components(p)

    p = figure(
        width=600, height=350, 
        tools="",
        toolbar_location=None,
        title='Weather and forecasts in {}, {}'.format(o.name, o.country),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.sizing_mode = 'scale_width'

    us='#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d ' +\
       '#ffad33 #ffa31a #ff9900 #e68a00 #cc7a00 #b36b00 #995c00 ' +\
       '#804d00 #663d00 #4d2e00 #331f00 #1a0f00'
    ls='#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 ' +\
       '#85adad #75a3a3 #669999 #5c8a8a #527a7a #476b6b #3d5c5c ' +\
       '#334d4d #293d3d #1f2e2e #141f1f #0a0f0f'

    #ls = '#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266'.split() ##ffb84d #ffad33 #ffa31a #ff9900'.split()
    #us = '#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 #85adad #75a3a3 #669999 #5c8a8a'.split()
    us = us.split()
    us = us[::-1]
    ls = ls.split()
    x = np.append(timed, timed[::-1])
    unp=1013.25
    lnp=999.918
    up=1086.5773
    lp=854.59638
    y = [lp + i * (lnp - lp) / len(ls) for i in range(0, len(ls) + 1)] +\
        [unp + i * (up - unp) / len(us) for i in range(0, len(us) + 1)]
    i = 0
    #import pdb; pdb.set_trace()
    for color in us + ['#ffffff'] + ls:
        p.patch(x, [y[i]]*len(timed) + [y[i+1]]*len(timed) , color=color)#, fill_alpha=0.2)
        i += 1

    for i in range(len(timed)):
        p.line([x[i],x[i]], [y[0],y[-1]], color='grey', line_width=.3)

    p.line(timed, presd, legend="Pressure, hpa", line_width=3)
    #p.line(timed, pressd, legend="Pressure(sea level), hpa", line_width=3, color='grey')
    #p.line(timed, presgd, legend="Pressure(ground level), hpa", line_width=3, color='green')

    script['pres'], div['pres'] = components(p)

    p = figure(
        width=600, height=350, 
        tools="",
        toolbar_location=None,
        title='Weather and forecasts in {}, {}'.format(o.name, o.country),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.sizing_mode = 'scale_width'
    p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm")
    script['prec'], div['prec'] = components(p)

    return {'o': o, 'sr': sr, 'st': st, 'fcs': fcs, 'script': script, 'div': div}
    
def draw_yah(c):
    ya = c.yahoo_set.latest('req_date')
    yql = json.loads(ya.yql_resp_text.replace("'",'"'))
    yy = {}
    yy['temp'] = float(yql['query']['results']['channel']['item']['condition']['temp'])
    yy['temp'] = "{0:.1f}".format((yy['temp'] - 32) * 5 / 9)
    yy['text'] = yql['query']['results']['channel']['item']['condition']['text']
    yy['date'] = yql['query']['results']['channel']['item']['condition']['date']
    yy['code'] = yql['query']['results']['channel']['item']['condition']['code']
    yy['winddir'] = yql['query']['results']['channel']['wind']['direction']
    yy['windspeed'] = float(yql['query']['results']['channel']['wind']['speed'])
    yy['windspeed'] = "{0:.2f}".format(yy['windspeed'] * 0.44704)
    yy['pressure'] = yql['query']['results']['channel']['atmosphere']['pressure']
    yy['humidity'] = yql['query']['results']['channel']['atmosphere']['humidity']
    yy['sunrise'] = yql['query']['results']['channel']['astronomy']['sunrise']
    yy['sunset'] = yql['query']['results']['channel']['astronomy']['sunset']

    fcs = []
    tempnd = []
    tempxd = []
    timed = []
    for f in ya.yahooforecast_set.order_by('id'):
        fd = json.loads(f.forecast_text.replace("'",'"'))

        tempnd.append((float(fd['low']) - 32) * 5 / 9)
        fd['min'] = "{0:.1f}".format(tempnd[-1])
        tempxd.append((float(fd['high']) - 32) * 5 / 9)
        fd['max'] = "{0:.1f}".format(tempxd[-1])

        fd['date'] = datetime.datetime.strptime(fd['date'], '%d %b %Y')
        timed.append(fd['date'])

        fcs.append(fd)

    script, div = {}, {}
    p = figure(
        width=600, height=350, 
        tools="",
        toolbar_location=None,
        title='Weather and forecasts in {}, {}'.format(ya.name, ya.country),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    #p.sizing_mode = 'scale_width'
    p.y_range = Range1d(start = min(tempnd) - 10, end = max(tempxd) + 10)
    x=np.append(timed, timed[::-1])
    y=np.append(tempnd, tempxd[::-1])
    p.patch(x, y, color='#7570B3', fill_alpha=0.2)

    script['temp'], div['temp'] = components(p)

    return {'y':ya, 'yy':yy, 'fcs':fcs, 'script':script, 'div':div}

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
            city.ds_yahoo = form.cleaned_data['ds_yahoo'] #request.POST['ds_yahoo']
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
        form = CityModelForm(initial={'name': city.name, 'ds_owm': city.ds_owm, 'ds_yahoo': city.ds_yahoo})

    return render(request, 'weather/city_detail_form.html', {'form': form, 'city': city})

class OWMView(generic.ListView): #(LoginRequiredMixin, generic.ListView):
    template_name = 'weather/owm_detail.html'
    context_object_name = 'owmforecast_list'
    
    def get_queryset(self):
        self.owm = get_object_or_404(OWM, id=self.kwargs['pk'])
        fcs = []
        for f in self.owm.owmforecast_set.all():
            fcs.append(json.loads(f.forecast_text.replace("'",'"')))
            fcs[-1]['main']['temp'] = round(float(fcs[-1]['main']['temp']) - 273.15, 1)
            fcs[-1]['main']['temp_min'] = round(float(fcs[-1]['main']['temp_min']) - 273.15, 1)
            fcs[-1]['main']['temp_max'] = round(float(fcs[-1]['main']['temp_max']) - 273.15, 1)
            fcs[-1]['main']['pressure'] = float(fcs[-1]['main']['pressure'])
            fcs[-1]['main']['sea_level'] = float(fcs[-1]['main']['sea_level'])
            fcs[-1]['main']['grnd_level'] = float(fcs[-1]['main']['grnd_level'])
            fcs[-1]['main']['humidity'] = int(fcs[-1]['main']['humidity'])
            fcs[-1]['wind']['speed'] = float(fcs[-1]['wind']['speed'])
            
            tprc = 0
            if 'snow' in fcs[-1] and '3h' in fcs[-1]['snow']:
               tprc += float(fcs[-1]['snow']['3h'])

            if 'rain' in fcs[-1] and '3h' in fcs[-1]['rain']:
                tprc += float(fcs[-1]['rain']['3h'])

            fcs[-1]['prec'] = tprc

            fcs[-1]['date'] = datetime.datetime.fromtimestamp(int(fcs[-1]['dt']), pytz.timezone('UTC'))
            fcs[-1]['date'] = fcs[-1]['date'].astimezone(pytz.timezone('Europe/Moscow'))

        return sorted(fcs, key=lambda x: x['date'])

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OWMView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['owm'] = self.owm
        return context

class YahooView(generic.ListView): #(LoginRequiredMixin, generic.ListView):
    template_name = 'weather/yahoo_detail.html'
    context_object_name = 'yahooforecast_list'
    
    def get_queryset(self):
        self.yahoo = get_object_or_404(Yahoo, id=self.kwargs['pk'])
        fcs = []
        for f in self.yahoo.yahooforecast_set.all():
            fcs.append(json.loads(f.forecast_text.replace("'",'"')))
            fcs[-1]['low'] = round((float(fcs[-1]['low']) - 32) * 5 / 9, 1)
            fcs[-1]['high'] = round((float(fcs[-1]['high']) - 32) * 5 / 9, 1)
            fcs[-1]['date'] = datetime.datetime.strptime(fcs[-1]['date'],"%d %b %Y")

        return sorted(fcs, key=lambda x: x['date'])

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(YahooView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['yahoo'] = self.yahoo
        return context
        
def cron(request):
    username = request.GET['username']
    password = request.GET['password']
    user = authenticate(username=username, password=password)

    context = dict()
    
    if user is None:
        context.update({
            'fail': '',
            'error': 'auth fail'
        })
        
        return render(request, 'weather/cron.html', context)

    login(request, user)

    c = City.objects.filter(turn=True).first()
    if c is None:
        City.objects.all().update(turn=True)
        c = City.objects.first()

    c.turn = False
    c.save()

    context.update({'city': {'name': c.name, 'ds_owm': c.ds_owm, 'ds_yahoo': c.ds_yahoo}})

    get_owm(request, context, c)
    get_yahoo(request, context, c)
    
    logout(request)
        
    return render(request, 'weather/cron.html', context)

def get_owm(request, context, c):
    resp = requests.get(c.ds_owm)
    for i in [1]:#,2,3,5]:
        if resp is None:
            time.sleep(1)
            context.update(
                {'owm': {
                    'fail': '',
                    'error': c.ds_owm + ': no response'
            }})
            continue

        pj = json.loads(resp.text)
        resp.close()
        
        if pj['cod'] != '200':
            time.sleep(1)
            context.update(
                {'owm': {
                    'fail': '',
                    'error': pj['cod'] + ', ' + pj['message']
                }})
            continue

        break
        
    else:
        owm = OWM()
        owm.message = context['owm']['error']
        owm.city = c
        owm.req_date = timezone.now()
        owm.save()
        logout(request)
        return
        
    context.update(
        {'owm': {
            'ok': '',
        }})

    owm = OWM()

    owm.iden = pj['city']['id']
    owm.name = pj['city']['name']
    owm.coord_lon = pj['city']['coord']['lon']
    owm.coord_lat = pj['city']['coord']['lat']
    owm.country = pj['city']['country']
    #owm.population = pj['city']['population']
    #owm.sys_population = pj['city']['sys']['population']

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

    return

def get_yahoo(request, context, c):
    resp = requests.get(c.ds_yahoo)

    if resp is None:
        context.update(
            {'yahoo': {
                'fail': '',
                'error': c.name + ' req fail'
                }})
        yah = Yahoo()
        yah.yql_resp_text = c.ds_yahoo + ': no response'
        yah.city = c
        yah.req_date = timezone.now()
        yah.save()
        
        return

    pj = json.loads(resp.text)

    context.update(
        {'yahoo': {
            'ok': '',
        }})
    yah = Yahoo()
    yah.name = pj['query']['results']['channel']['location']['city']
    yah.coord_lat = pj['query']['results']['channel']['item']['lat']
    yah.coord_lon = pj['query']['results']['channel']['item']['long']
    yah.country = pj['query']['results']['channel']['location']['country']
    yah.region = pj['query']['results']['channel']['location']['region']
    yah.yql_resp_text = resp.text
    resp.close()
    yah.city = c
    yah.req_date = timezone.now()
    yah.save()

    for fcs in pj['query']['results']['channel']['item']['forecast']:
        yah_forecast = YahooForecast()

        yah_forecast.yahoo = yah
        yah_forecast.forecast_text = fcs
        yah_forecast.save()

    return
    
class RequestTodayArchiveView(TodayArchiveView): #(LoginRequiredMixin, TodayArchiveView):
    #queryset = RequestArchive.objects.all()
    #date_field = "req_date"
    allow_future = True
    make_object_list = True
    allow_empty = True
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        req_date = timezone.now()
        kwargs['req_date'] = timezone.now()
        kwargs['calendar'] = SideBarCalendar('weather:archive_day', req_date).formatmonth()
        kwargs['city_day_conds'] = draw_cdc(self, req_date)

        return super(RequestTodayArchiveView, self).get_context_data(**kwargs)

class RequestDayArchiveView(DayArchiveView): #(LoginRequiredMixin, DayArchiveView):
    queryset = RequestArchive.objects.all()
    date_field = "req_date"
    allow_future = True
    make_object_list = True
    allow_empty = True
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        req_date = timezone.datetime(int(self.get_year()), int(self.get_month()), int(self.get_day()))
        kwargs['calendar'] = SideBarCalendar('weather:archive_day', req_date).formatmonth()
        kwargs['city_day_conds'] = draw_cdc(self, req_date)
        
        return super(RequestDayArchiveView, self).get_context_data(**kwargs)

def draw_cdc(rdav, req_date):
    city_list = list()

    if 'username' in rdav.kwargs and \
       rdav.kwargs['username'] == rdav.request.user.username:

        username = rdav.request.user.username
        cities = get_list_or_404(City, user_name=username)
    else:
        cities = get_list_or_404(City)

    for c in sorted(cities, key=lambda x: x.name):
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
        for o in c.owm_set.filter( \
            req_date__year=req_date.year, \
            req_date__month=req_date.month, \
            req_date__day=req_date.day).order_by('req_date'):

            f = o.owmforecast_set.first()
            if f is None:
                pass

            else:
                fd = json.loads(f.forecast_text.replace("'",'"'))

                tempd.append(float(fd['main']['temp']) - 273.15)
                tempnd.append(float(fd['main']['temp_min']) - 273.15)
                tempxd.append(float(fd['main']['temp_max']) - 273.15)
                presd.append(float(fd['main']['pressure']))
                pressd.append(float(fd['main']['sea_level']))
                presgd.append(float(fd['main']['grnd_level']))
                humid.append(float(fd['main']['humidity']))
                windd.append(float(fd['wind']['speed']))

                tprc = 0
                if 'snow' in fd and '3h' in fd['snow']:
                    tprc += float(fd['snow']['3h'])

                if 'rain' in fd and '3h' in fd['rain']:
                    tprc += float(fd['rain']['3h'])

                precd.append(tprc)

                timed.append(datetime.datetime.fromtimestamp(int(fd['dt']), timezone.utc))

        script, div = {}, {}
        
        p = figure(
            width=440, height=250, 
            tools="",
            toolbar_location=None,
            title='Weather in {}'.format(c.name),
            x_axis_type="datetime",
            x_axis_label='', y_axis_label=''
            )
        p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                            end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
        p.extra_y_ranges = {"prec": Range1d(start=0, end=max([0]+precd))}
        p.add_layout(LinearAxis(y_range_name="prec"), 'right')
        x=np.append(timed, timed[::-1])
        y=np.append(tempnd, tempxd[::-1])
        p.patch(x, y, color='#7570B3', fill_alpha=0.2)
        p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm", color="grey", y_range_name="prec")
        p.line(timed, tempd, legend="Temperature, °C", line_width=3, color='blue')
        script['temp'], div['temp'] = components(p)

        p = figure(
            width=440, height=250, 
            tools="",
            toolbar_location=None,
            title='Weather in {}'.format(c.name),
                x_axis_type="datetime",
                x_axis_label='', y_axis_label=''
            )
        us = '#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d ' +\
             '#ffad33 #ffa31a #ff9900 #e68a00 #cc7a00 #b36b00 #995c00 ' +\
             '#804d00 #663d00 #4d2e00 #331f00 #1a0f00'
        ls = '#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 ' +\
             '#85adad #75a3a3 #669999 #5c8a8a #527a7a #476b6b #3d5c5c ' +\
             '#334d4d #293d3d #1f2e2e #141f1f #0a0f0f'
        us = us.split()
        us = us[::-1]
        ls = ls.split()
        x = np.append(timed, timed[::-1])
        unp = 70
        lnp = 40
        up = 100
        lp = 0
        y = [lp + i * (lnp - lp) / len(ls) for i in range(0, len(ls) + 1)] +\
            [unp + i * (up - unp) / len(us) for i in range(0, len(us) + 1)]
        i = 0
        for color in us + ['#ffffff'] + ls:
            p.patch(x, [y[i]]*len(timed) + [y[i+1]]*len(timed) , color=color)#, fill_alpha=0.2)
            i += 1
                
        p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                            end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
        p.line(timed, humid, legend="Humidity, %", line_width=3)
        script['humi'], div['humi'] = components(p)

        p = figure(
            width=440, height=250, 
            tools="",
            toolbar_location=None,
            title='Weather in {}'.format(c.name),
            x_axis_type="datetime",
            x_axis_label='', y_axis_label=''
            )
        p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                            end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
        p.line(timed, windd, legend="Wind, m/s", line_width = 4)
        script['wind'], div['wind'] = components(p)

        p = figure(
            width=440, height=250, 
            tools="",
            toolbar_location=None,
            title='Weather in {}'.format(c.name),
            x_axis_type="datetime",
            x_axis_label='', y_axis_label=''
            )
        us = '#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d ' +\
             '#ffad33 #ffa31a #ff9900 #e68a00 #cc7a00 #b36b00 #995c00 ' +\
             '#804d00 #663d00 #4d2e00 #331f00 #1a0f00'
        ls = '#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 ' +\
             '#85adad #75a3a3 #669999 #5c8a8a #527a7a #476b6b #3d5c5c ' +\
             '#334d4d #293d3d #1f2e2e #141f1f #0a0f0f'
        us = us.split()
        us = us[::-1]
        ls = ls.split()
        x = np.append(timed, timed[::-1])
        unp = 1013.25
        lnp = 999.918
        up = 1086.5773
        lp = 854.59638
        y = [lp + i * (lnp - lp) / len(ls) for i in range(0, len(ls) + 1)] +\
            [unp + i * (up - unp) / len(us) for i in range(0, len(us) + 1)]
        i = 0
        for color in us + ['#ffffff'] + ls:
            p.patch(x, [y[i]]*len(timed) + [y[i+1]]*len(timed) , color=color)#, fill_alpha=0.2)
            i += 1

        p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                            end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
        p.line(timed, presd, legend="Pressure, hpa", line_width=3)
        #p.line(timed, pressd, legend="Pressure(sea level), hpa", line_width=3, color='grey')
        #p.line(timed, presgd, legend="Pressure(ground level), hpa", line_width=3, color='green')
        script['pres'], div['pres'] = components(p)

        # p = figure(
        #     width=440, height=250, 
        #     tools="",
        #     toolbar_location=None,
        #     title='Weather in {}'.format(c.name),
        #     x_axis_type="datetime",
        #     x_axis_label='', y_axis_label=''
        #     )
        # p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
        #                     end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
        # p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm")
        # script['prec'], div['prec'] = components(p)

        yad = get_yah_d(rdav, req_date, c)
            
        city_list.append({'city': c,
                          'owm': {'script': script, 'div': div},
                          'yahoo': {'script': yad['script'], 'div': yad['div']}})

    return city_list

def get_yah_d(rdav, req_date, c):
    tempd = []
    windd = []
    presd = []
    humid = []
    precd = []
    timed = []
    
    for o in c.yahoo_set.filter( \
            req_date__year=req_date.year, \
            req_date__month=req_date.month, \
            req_date__day=req_date.day).order_by('req_date'):

        yql = json.loads(o.yql_resp_text.replace("'",'"'))

        conds = parse_yql(yql)
        
        tempd.append(conds['temp'])
        windd.append(conds['windspeed'])
        presd.append(conds['pressure'])
        humid.append(conds['humidity'])
        timed.append(conds['date'])
        precd.append(0)

    script, div = {}, {}
        
    p = figure(
        width=440, height=250, 
        tools="",
        toolbar_location=None,
        title='Weather in {}'.format(c.name),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                        end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
    p.extra_y_ranges = {"prec": Range1d(start=0, end=max([0]+precd))}
    p.add_layout(LinearAxis(y_range_name="prec"), 'right')
    p.vbar(x=timed, width=5000000, top=precd, legend="Precipitation, mm", color="grey", y_range_name="prec")
    p.line(timed, tempd, legend="Temperature, °C", line_width=3, color='blue')
    script['temp'], div['temp'] = components(p)

    p = figure(
        width=440, height=250, 
        tools="",
        toolbar_location=None,
        title='Weather in {}'.format(c.name),
            x_axis_type="datetime",
            x_axis_label='', y_axis_label=''
        )
    us = '#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d ' +\
         '#ffad33 #ffa31a #ff9900 #e68a00 #cc7a00 #b36b00 #995c00 ' +\
         '#804d00 #663d00 #4d2e00 #331f00 #1a0f00'
    ls = '#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 ' +\
         '#85adad #75a3a3 #669999 #5c8a8a #527a7a #476b6b #3d5c5c ' +\
         '#334d4d #293d3d #1f2e2e #141f1f #0a0f0f'
    us = us.split()
    us = us[::-1]
    ls = ls.split()
    x = np.append(timed, timed[::-1])
    unp = 70
    lnp = 40
    up = 100
    lp = 0
    y = [lp + i * (lnp - lp) / len(ls) for i in range(0, len(ls) + 1)] +\
        [unp + i * (up - unp) / len(us) for i in range(0, len(us) + 1)]
    i = 0
    for color in us + ['#ffffff'] + ls:
        p.patch(x, [y[i]]*len(timed) + [y[i+1]]*len(timed) , color=color)#, fill_alpha=0.2)
        i += 1

    p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                        end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
    p.line(timed, humid, legend="Humidity, %", line_width=3)
    script['humi'], div['humi'] = components(p)

    p = figure(
        width=440, height=250, 
        tools="",
        toolbar_location=None,
        title='Weather in {}'.format(c.name),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                        end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
    p.line(timed, windd, legend="Wind, m/s", line_width = 4)
    script['wind'], div['wind'] = components(p)

    p = figure(
        width=440, height=250, 
        tools="",
        toolbar_location=None,
        title='Weather in {}'.format(c.name),
        x_axis_type="datetime",
        x_axis_label='', y_axis_label=''
        )
    us = '#fff5e6 #ffebcc #ffe0b3 #ffd699 #ffcc80 #ffc266 #ffb84d ' +\
         '#ffad33 #ffa31a #ff9900 #e68a00 #cc7a00 #b36b00 #995c00 ' +\
         '#804d00 #663d00 #4d2e00 #331f00 #1a0f00'
    ls = '#f0f5f5 #e0ebeb #d1e0e0 #c2d6d6 #b3cccc #a3c2c2 #94b8b8 ' +\
         '#85adad #75a3a3 #669999 #5c8a8a #527a7a #476b6b #3d5c5c ' +\
         '#334d4d #293d3d #1f2e2e #141f1f #0a0f0f'
    us = us.split()
    us = us[::-1]
    ls = ls.split()
    x = np.append(timed, timed[::-1])
    unp = 1013.25
    lnp = 999.918
    up = 1086.5773
    lp = 854.59638
    y = [lp + i * (lnp - lp) / len(ls) for i in range(0, len(ls) + 1)] +\
        [unp + i * (up - unp) / len(us) for i in range(0, len(us) + 1)]
    i = 0
    for color in us + ['#ffffff'] + ls:
        p.patch(x, [y[i]]*len(timed) + [y[i+1]]*len(timed) , color=color)#, fill_alpha=0.2)
        i += 1

    p.x_range = Range1d(start=datetime.datetime(req_date.year,req_date.month,req_date.day,0,0), \
                        end=datetime.datetime(req_date.year,req_date.month,req_date.day,23,59))
    p.line(timed, presd, legend="Pressure, hpa", line_width=3)
    #p.line(timed, pressd, legend="Pressure(sea level), hpa", line_width=3, color='grey')
    #p.line(timed, presgd, legend="Pressure(ground level), hpa", line_width=3, color='green')
    script['pres'], div['pres'] = components(p)

    return {'script':script, 'div':div}

def parse_yql(yql):
    conds = {}
    conds['temp'] = float(yql['query']['results']['channel']['item']['condition']['temp'])
    conds['temp'] = round((conds['temp'] - 32) * 5 / 9, 1)
    conds['text'] = yql['query']['results']['channel']['item']['condition']['text']
    conds['date'] = yql['query']['results']['channel']['item']['condition']['date']
    #'Wed, 01 Mar 2017 09:00 AM MSK'
    #conds['date'] = datetime.datetime.strptime(conds['date'][:25], '%a, %d %b %Y %I:%M %p')# %Z')
    conds['date'] = parser.parse(conds['date'])
    conds['winddir'] = yql['query']['results']['channel']['wind']['direction']
    conds['windspeed'] = round(float(yql['query']['results']['channel']['wind']['speed']) * 0.44704, 2)
    conds['pressure'] = round(float(yql['query']['results']['channel']['atmosphere']['pressure']), 2)
    conds['humidity'] = round(float(yql['query']['results']['channel']['atmosphere']['humidity']), 0)
    conds['sunrise'] = yql['query']['results']['channel']['astronomy']['sunrise']
    conds['sunset'] = yql['query']['results']['channel']['astronomy']['sunset']

    return conds
