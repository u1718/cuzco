from django.conf.urls import url

from . import views
from .models import RequestArchive

app_name = 'weather'

urlpatterns = [
    # ex: /weather/
    url(r'^$', views.CitiesView.as_view(), name='cities'),
    # ex: /weather/uname
    url(r'^u(?P<username>\w+)/$', views.CitiesView.as_view(), name='cities'),

    # ex: /weather/2/
    url(r'^(?P<pk>[0-9]+)/$', views.CityView.as_view(), name='city_view'),
    # ex: /weather/upd/2/
    url(r'^upd/(?P<city_id>[0-9]+)/$', views.city_update, name='city_update'),
    
    # ex: /weather/(owm|yahoo)fc/6/
    url(r'^owmfc/(?P<pk>[0-9]+)/$', views.OWMView.as_view(), name='owm_view'),
    url(r'^yahoofc/(?P<pk>[0-9]+)/$', views.YahooView.as_view(), name='yahoo_view'),

    # ex: /weather/cron/99/
    url(r'^cron/$', views.cron, name='cron'),

    # ex: /weather/gr/
    url(r'^gr/(?P<owm_id>[0-9]+)/$', views.gr, name='gr'),
    
    # ex: /weather/archive/
    url(r'^archive/$',
        views.RequestTodayArchiveView.as_view(model=RequestArchive, date_field="req_date"),
        name="archive"),
    # ex: /weather/archive/1970/1/1/
    url(r'^archive/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        views.RequestDayArchiveView.as_view(month_format='%m'),
        name="archive_day"),
    ]
