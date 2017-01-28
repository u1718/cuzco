from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import generic
from django.utils import timezone
from django.views.generic.dates import TodayArchiveView, DayArchiveView

import requests
import json

from .models import City, OWM, OWMForecast
from .sbcalendar import SideBarCalendar
from .forms import CityModelForm

class CitiesView(LoginRequiredMixin, generic.ListView):
    #login_url = ''
    #redirect_field_name = ''
    #template_name = 'weather/city_list.html'
    #context_object_name = 'city_list' == object_list
    paginate_by = 20

    def get_queryset(self):
        """Return requested cities."""
        return City.objects.order_by('name')

class CityView(LoginRequiredMixin, generic.ListView):
    template_name = 'weather/city_detail.html'
    context_object_name = 'owm_list'
    paginate_by = 20
    
    def get_queryset(self):
        self.city = get_object_or_404(City, id=self.kwargs['pk'])
        return self.city.owm_set.all()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CityView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['city'] = self.city
        return context
        
class CityForm(LoginRequiredMixin, generic.DetailView):
    model = City
    template_name = 'weather/city_detail_form.html'
    
    def get_context_data(self, **kwargs):
        kwargs['form'] = CityModelForm()

        return super(CityForm, self).get_context_data(**kwargs)
    
@login_required    
def city_update(request, city_id):
    city = get_object_or_404(City, pk=city_id)
    city.name = request.POST['name']
    city.ds_owm = request.POST['ds_owm']
    city.save()
    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('weather:owm_view', args=(city.id,)))

class OWMView(LoginRequiredMixin, generic.ListView):
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
            
        if not True:
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

class OWMTodayArchiveView(LoginRequiredMixin, TodayArchiveView):
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


class OWMDayArchiveView(LoginRequiredMixin, DayArchiveView):
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
