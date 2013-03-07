from django.conf.urls import patterns, url

from wlether import views

urlpatterns = patterns('',
    # ex: /wlether/
    url(r'^$', views.index, name='index'),
    # ex: /wlether/5/
    url(r'^(?P<scan_id>\d+)/$', views.detail, name='detail'),
    # ex: /wlether/5/results/
    url(r'^(?P<scan_id>\d+)/results/$', views.results, name='results'),
    # ex: /wlether/5/vote/
    url(r'^(?P<scan_id>\d+)/vote/$', views.vote, name='vote'),
)
