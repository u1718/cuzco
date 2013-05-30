from django.conf.urls import patterns, url
from django.views.generic.dates import ArchiveIndexView

from wlether import views

from django.views.generic import DetailView, ListView
from django.views.generic.dates import DateDetailView

from wlether.models import Scan, APoint

urlpatterns = patterns('',
    # ex: /wlether/
    url(r'^$', views.today, name='today'),
    # ex: /wlether/5/
    url(r'^(?P<pk>\d+)/$', views.ScanDetail.as_view(), name="scan_detail"),
    # ex: /wlether/5/5/detail/
    url(r'^(?P<scan_id>\d+)/(?P<apoint_id>\d+)/detail/$', views.apoint_detail, name='apoint_detail'),
    # ex: /wlether/1234/12/12
    url(r'^(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        views.ScanDayArchive.as_view(month_format='%m'),
        name="archive_day"),

    url(r'^mpl', views.test_matplotlib, name='test_matplotlib'),
    url(r'^gr/(?P<scan_year>\d{4})/(?P<scan_month>\d+)/(?P<scan_day>\d+)/$', views.gr, name='gr'),
    url(r'^gr_aps_sl/(?P<scan_year>\d{4})/(?P<scan_month>\d+)/(?P<scan_day>\d+)/$', views.gr_aps_sl, name='gr_aps_sl'),
    url(r'^aps_pie/(?P<scan_year>\d{4})/(?P<scan_month>\d+)/(?P<scan_day>\d+)/$', views.aps_pie, name='aps_pie'),
    url(r'^clndr/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', views.calendar, name='calendar'),
    url(r'^(?P<year>\d+)/(?P<month>[-\w]+)/(?P<day>\d+)/(?P<pk>\d+)/$',
        DateDetailView.as_view(model=Scan, date_field="scan_time"),
        name="archive_date_detail"),
    url(r'^today/$',
        views.ScanTodayArchiveView.as_view(),
        name="archive_today"),
    url(r'^(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
        views.ScanDayArchiveView.as_view(month_format='%m'),
        name="archive_day"),
    url(r'^(?P<year>\d{4})/week/(?P<week>\d+)/$',
        views.ScanWeekArchiveView.as_view(),
        name="archive_week"),
    # Example: /2012/08/
    url(r'^(?P<year>\d{4})/(?P<month>\d+)/$',
        views.ScanMonthArchiveView.as_view(month_format='%m'),
        name="archive_month_numeric"),
    # Example: /2012/aug/
    url(r'^(?P<year>\d{4})/(?P<month>[-\w]+)/$',
        views.ScanMonthArchiveView.as_view(),
        name="scan_month"),
    url(r'^y(?P<year>\d{4})/$',
        views.ScanYearArchiveView.as_view(),
        name="archive_year_archive"),
    url(r'archive/$',
        ArchiveIndexView.as_view(model=Scan, date_field="scan_time"),
        name="scan_archive"),
    #url(r'^$', views.index, name='index'), # comment out to use ListView
    url(r'^$',
        views.IndexView.as_view(
            queryset = Scan.objects.order_by('-scan_time')[:20],
            template_name = 'wlether/index.html',
            context_object_name = 'latest_scan_list'),
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
