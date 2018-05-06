from django.urls import path

from . import views
from .models import RequestArchive

app_name = 'weather'

urlpatterns = [
    # ex: /weather/
    path('', views.CitiesView.as_view(), name='cities'),
    # # ex: /weather/uname
    # url(r'^u(?P<username>\w+)/$', views.CitiesView.as_view(), name='cities'),

    # ex: /weather/2/
    path('<int:pk>/', views.CityView.as_view(), name='city_view'),
    # ex: /weather/upd/2/
    path('upd/<int:city_id>/', views.city_update, name='city_update'),
    
    # ex: /weather/(owm|yahoo)fc/6/
    path('owmfc/<int:pk>/', views.OWMView.as_view(), name='owm_view'),
    path('yahoofc/<int:pk>/', views.YahooView.as_view(), name='yahoo_view'),

    # ex: /weather/cron?username=<>&password=<>
    path('cron/', views.cron, name='cron'),

    # ex: /weather/archive/
    path('archive/',
        views.RequestTodayArchiveView.as_view(model=RequestArchive, date_field="req_date"),
        name="archive"),
    # ex: /weather/archive/1970/1/1/
    path('archive/<int:year>/<int:month>/<int:day>/',
        views.RequestDayArchiveView.as_view(month_format='%m'),
        name="archive_day"),
    ]
