from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

import requests
import json

from .models import City, OWM, OWMForecast

class CityView(LoginRequiredMixin, generic.ListView):
    #login_url = ''
    #redirect_field_name = ''
    #template_name = 'weather/city_list.html'
    #context_object_name = 'city_list'

    def get_queryset(self):
        """Return requested cities."""
        return City.objects.order_by('name')

class OWMView(generic.DetailView):
    model = City
    #template_name = 'weather/city_detail.html'

class OWMForecastView(generic.DetailView):
    model = OWM
    #template_name = 'weather/owm_detail.html'

def cron(request):
    username = request.GET['username']
    password = request.GET['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        
        context = dict()
        
        c = City.objects.filter(turn=True).first()
        if c is None:
            City.objects.all().update(turn=True)
            c = City.objects.filter(turn=True).first()

        c.turn = False
        c.save()
            
        resp = requests.get(c.ds_owm)

        # #http://api.openweathermap.org/data/2.5/forecast/city?id=498698&APPID=775670b8133c08911511535c6b1dfbdf
        # url = 'http://api.openweathermap.org/data/2.5/forecast/city'
        # params = {
        #     'id':r'498698',
        #     'appid':r'775670b8133c08911511535c6b1dfbdf'
        # }

        # resp = requests.get(url, params = params)

        # with open('./owm.data') as f:
        #     w = f.read()

        # class Resp:
        #     def __init__(self, t):
        #         self.text = t

        # resp = Resp(w)

        if resp is not None:

            pj = json.loads(resp.text)

            if pj['cod'] == '0':
                context = {
                    'fail': '',
                    'error': pj['message']
                }
                owm = OWM()

                owm.message = pj['message']

                owm.city = c
                owm.req_date = timezone.now()

                owm.save()

            else:
                context = {
                    'ok': '',
                    'root': pj.keys(),
                    'city': pj['city'],
                    'list': pj['list'],
                }

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
            context = {
                'fail': '',
                'error': 'req fail'
            }

            owm = OWM()

            owm.message = 'No Response'

            owm.city = c
            owm.req_date = timezone.now()

            owm.save()

        logout(request)
        
    else:
        context = {
            'fail': '',
            'error': 'auth fail'
        }
        
    return render(request, 'weather/cron.html', context)



