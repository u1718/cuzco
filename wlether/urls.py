from django.conf.urls import patterns, url

from wlether import views

urlpatterns = patterns('',
    # ex: /wlether/
    url(r'^$', views.index, name='index'),
    # ex: /wlether/5/
    url(r'^(?P<scan_id>\d+)/$', views.detail, name='detail'),
    # ex: /wlether/5/5/details/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/details/$', views.details, name='details'),
    # ex: /wlether/5/results/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/results/$', views.results, name='results'),
    # ex: /wlether/5/5/collect/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/collect/$', views.collect, name='collect'),
)
