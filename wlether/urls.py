from django.conf.urls import patterns, url

from wlether import views

from django.views.generic import DetailView, ListView
from wlether.models import Scan

urlpatterns = patterns('',
    # ex: /wlether/
    url(r'^$', views.index, name='index'), # comment out to use ListView
    url(r'^$',
        ListView.as_view(
            queryset=Scan.objects.order_by('-scan_time')[:5],
            context_object_name='latest_scan_list',
            template_name='wlether/index.html'),
        name='index'),
    # ex: /wlether/5/
    url(r'^(?P<scan_id>\d+)/$', views.detail, name='detail'),
    # ex: /wlether/5/5/details/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/details/$', views.details, name='details'),
    # ex: /wlether/5/results/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/results/$', views.results, name='results'),
    # ex: /wlether/5/5/collect/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/collect/$', views.collect, name='collect'),
)
# from django.conf.urls import patterns, url
# from django.views.generic import DetailView, ListView
# from polls.models import Poll

# urlpatterns = patterns('',
#     url(r'^$',
#         ListView.as_view(
#             queryset=Poll.objects.order_by('-pub_date')[:5],
#             context_object_name='latest_poll_list',
#             template_name='polls/index.html'),
#         name='index'),
#     url(r'^(?P<pk>\d+)/$',
#         DetailView.as_view(
#             model=Poll,
#             template_name='polls/detail.html'),
#         name='detail'),
#     url(r'^(?P<pk>\d+)/results/$',
#         DetailView.as_view(
#             model=Poll,
#             template_name='polls/results.html'),
#         name='results'),
#     url(r'^(?P<poll_id>\d+)/vote/$', 'polls.views.vote', name='vote'),
# )
