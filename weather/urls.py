from django.conf.urls import url

from . import views

app_name = 'weather'

urlpatterns = [
    # ex: /weather/
    url(r'^$', views.CityView.as_view(), name='city_view'),
    # ex: /weather/2/
    url(r'^(?P<pk>[0-9]+)/$', views.OWMView.as_view(), name='owm_view'),
    # ex: /weather/fcs/6/
    url(r'^fcs/(?P<pk>[0-9]+)/$', views.OWMForecastView.as_view(), name='owm_forecast_view'),
    # ex: /weather/cron/
    url(r'^cron/$', views.cron, name='cron'),
    
]
