from django.conf.urls import url

from . import views
from .models import OWM

app_name = 'weather'

urlpatterns = [
    # ex: /weather/
    url(r'^$', views.CitiesView.as_view(), name='cities'),

    # ex: /weather/2/
    url(r'^(?P<pk>[0-9]+)/$', views.CityView.as_view(), name='city_view'),
    # ex: /weather/upd/2/
    url(r'^upd/(?P<city_id>[0-9]+)/$', views.city_update, name='city_update'),
    
    # ex: /weather/fc/6/
    url(r'^fc/(?P<pk>[0-9]+)/$', views.OWMView.as_view(), name='owm_view'),

    # ex: /weather/cron/
    url(r'^cron/$', views.cron, name='cron'),
    
    # ex: /weather/archive/
    url(r'^archive/$',
        views.OWMTodayArchiveView.as_view(model=OWM, date_field="req_date"),
        name="archive"),
    # ex: /weather/archive/1970/1/1/
    url(r'^archive/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        views.OWMDayArchiveView.as_view(month_format='%m'),
        name="archive_day"),
    ]
