
# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
# from django.template import Context, loader
from django.shortcuts import render, get_object_or_404
# from django.http import Http404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.dates import YearArchiveView, MonthArchiveView, WeekArchiveView, DayArchiveView, TodayArchiveView
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.utils.safestring import mark_safe

from wlether.models import Scan, APoint
from wlether.sbclndr import SbCalendar

from calendar import HTMLCalendar

import base64

def basic_http_auth(f):
    def wrap(request, *args, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION', False):
            authtype, auth = request.META['HTTP_AUTHORIZATION'].split(' ')
            auth = base64.b64decode(auth)
            username, password = auth.split(':')
            if username == 'xuu' and password == 'uXXUxx':
                return f(request, *args, **kwargs)
            else:
                r = HttpResponse("Auth Required", status = 401)
                r['WWW-Authenticate'] = 'Basic realm="p`bat"'
                return r
        r = HttpResponse("Auth Required", status = 401)
        r['WWW-Authenticate'] = 'Basic realm="p`bat"'
        return r
        
    return wrap
    
@basic_http_auth
def today(request):
    scan_list = Scan.objects.order_by('-scan_time')
    paginator = Paginator(scan_list, 30)
    now = timezone.now()
    cal_curmonth = SbCalendar('wlether:archive_day', now).formatmonth()

    page = request.GET.get('page')
    try:
        scans = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        scans = paginator.page(1)
        #TODO: <meta http-equiv="refresh" content="60" > 
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        scans = paginator.page(paginator.num_pages)

    return render(request,'wlether/today.html', {"scans": scans,
                                                 "calendar": cal_curmonth,
                                                 "scan_date": now})

class ScanDetail(SingleObjectMixin, ListView):
    paginate_by = 20
    template_name = "wlether/scan_detail.html"

    def get_context_data(self, **kwargs):
        kwargs['scan'] = self.object
        scan_date = self.object.scan_time
        cal_curmonth = SbCalendar('wlether:archive_day', scan_date).formatmonth()
        kwargs['scan_date'] = scan_date
        kwargs['calendar'] = cal_curmonth
        return super(ScanDetail, self).get_context_data(**kwargs)

    def get_queryset(self):
        self.object = self.get_object(Scan.objects.all())
        return self.object.apoint_set.all()

    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))

@basic_http_auth
def apoint_detail(request, scan_id, apoint_id):
    apoint = APoint.objects.get(pk=apoint_id)
    scan_date = Scan.objects.get(pk=scan_id).scan_time
    cal_curmonth = SbCalendar('wlether:archive_day', scan_date).formatmonth()
    context = {'scan_id': scan_id, 'apoint': apoint, 'scan_date': scan_date, 'calendar': cal_curmonth}
    return render(request, 'wlether/apoint_detail.html', context)

class ScanDayArchive(DayArchiveView):
    queryset = Scan.objects.all()
    date_field = "scan_time"
    make_object_list = True
    allow_future = True
    allow_empty = True
    paginate_by = 20

    def get_context_data(self, **kwargs):
        scan_date = timezone.datetime(int(self.get_year()), int(self.get_month()), int(self.get_day()))
        cal_curmonth = SbCalendar('wlether:archive_day', scan_date).formatmonth()
        kwargs['scan_date'] = scan_date
        kwargs['calendar'] = cal_curmonth

        return super(ScanDayArchive, self).get_context_data(**kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))

from pylab import figure, axes, pie, title, plot, get_current_fig_manager, close, legend, text
from matplotlib.backends.backend_agg import FigureCanvasAgg
import PIL, PIL.Image, StringIO


from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

@basic_http_auth
def gr_aps_sl(request, scan_year, scan_month, scan_day):
    scs=Scan.objects.filter(scan_time__year = scan_year).filter(scan_time__month = scan_month).filter(scan_time__day = scan_day)

    colorlist=[
        'blue','green','red','cyan','magenta','yellow','white','aquamarine','azure','beige','bisque','brown','burlywood','chartreuse','chocolate','coral','cornsilk','firebrick','gainsboro','gold','goldenrod','gray','grey','honeydew','ivory','khaki','lavender','lime','linen','maroon','moccasin','navy','olive','orange','orchid','peru','pink','plum','purple','salmon','seashell','sienna','snow','tan','thistle','tomato','turquoise','violet','wheat']
    fig = Figure(figsize=(46,16))
    ax=fig.add_subplot(111)
    ta=timezone.datetime(int(scan_year), int(scan_month), int(scan_day))
    tn=ta.replace(tzinfo=timezone.utc)
    x=[tn+timezone.timedelta(minutes=i) for i in xrange(24 * 60)]
    dapssl = dict()
    for s in scs:
        for ap in s.apoint_set.all():
            k = ap.ssid
            if len(k) == 0: k = ap.bssid
            if not dapssl.has_key(k): dapssl[k] = [None for i in range(24 * 60)]
            dapssl[k][(s.scan_time-tn).seconds / 60] = ap.signal_level

    i = 0
    for k in dapssl:
        ax.plot(x, dapssl[k], '.', color=colorlist[i])
        i += 1

    ax.legend(dapssl.keys())
        
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    fig.clear()
    return response
    
@basic_http_auth
def aps_pie(request, scan_year, scan_month, scan_day):
    scs=Scan.objects.filter(scan_time__year = scan_year).filter(scan_time__month = scan_month).filter(scan_time__day = scan_day)

    aps = dict()
    tapr = 0
    for s in scs:
        for ap in s.apoint_set.all():
            tapr += 1
            k = ap.ssid
            if len(k) == 0: k = ap.bssid
            if aps.has_key(k):
                aps[k] += 1
            else:
                aps[k] = 1

    apsp = dict()
    apsp['Other'] = 0
    apso = list()
    for a in aps:
        if (aps[a] / float(tapr)) < .01:
            apsp['Other'] += aps[a]
            apso.append('%s: %.2f%%' % (a,aps[a] / float(tapr) * 100))
        else:
            apsp[a] = aps[a]
    
    f = figure(figsize=(16,16))
    ax = axes([0.1, 0.1, 0.8, 0.8])
    apsp['Other:\n-'+'\n-'.join(apso)] = apsp['Other']
    del apsp['Other']
    
    labels = apsp.keys()
    fracs = apsp.values()
    e = [0 for i in xrange(len(fracs))]
    from operator import itemgetter
    fmin = min(enumerate(fracs), key=itemgetter(1))[0]
    fmax = max(enumerate(fracs), key=itemgetter(1))[0]
    e[fmin] = 0.03
    e[fmax] = 0.05
    explode=tuple(e)
    colorlist=[
        'aquamarine','azure','beige','bisque','blue','brown','burlywood','chartreuse','chocolate','coral','cornsilk','cyan','firebrick','gainsboro','gold','goldenrod','gray','green','grey','honeydew','ivory','khaki','lavender','lime','linen','magenta','maroon','moccasin','navy','olive','orange','orchid','peru','pink','plum','purple','red','salmon','seashell','sienna','snow','tan','thistle','tomato','turquoise','violet','wheat','white','yellow']
    colorlist=['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'gray', 'white']
    import random
    random.shuffle(colorlist)
    colortuple=tuple(colorlist)
    p = pie(fracs, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, colors=colortuple)
        #    'Red','Green','Yellow','Blue','Magenta','Cyan','White','Gray','Darkgray','Brown'))
    title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})
    legend(loc='best')
    
    canvas = FigureCanvasAgg(f)    
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    f.clear()
    return response
        
@basic_http_auth
def gr(request, scan_year, scan_month, scan_day):
    scs=Scan.objects.filter(scan_time__year = scan_year).filter(scan_time__month = scan_month).filter(scan_time__day = scan_day)

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    fig = Figure(figsize=(16,6))
    ax=fig.add_subplot(111)
    y=[None for i in range(24 * 60)]
    ta=timezone.datetime(int(scan_year), int(scan_month), int(scan_day))
    tn=ta.replace(tzinfo=timezone.utc)
    x=[tn+timezone.timedelta(minutes=i) for i in xrange(24 * 60)]
    for s in scs:
        y[(s.scan_time-tn).seconds / 60]=s.apoint_set.count()

    ax.plot(x, y, '.')
    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)
    fig.clear()
    return response
    
@basic_http_auth
def gr1(request):
    scs=Scan.objects.all()
    x = []
    y = []
    i = -1
    for s in scs:
        i += 1
        x.append(i)
        y.append(scs[i].apoint_set.count())

    figure(1, figsize=(26,6))
    plot(x,y)

    # Store image in a string buffer
    buffer = StringIO.StringIO()
    canvas = get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.fromstring("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    close()
 
    # Send buffer in a http response the the browser with the mime type image/png set
    return HttpResponse(buffer.getvalue(), mimetype="image/png")

@basic_http_auth
def test_matplotlib(request):
    f = figure(1, figsize=(6,6))
    ax = axes([0.1, 0.1, 0.8, 0.8])
    labels = 'Frogs', 'Hogs', 'Dogs', 'Logs', 'Mocks'
    fracs = [15,30,45,7,3]
    explode=(0, 0.05, 0, 0, 0.03)
    pie(fracs, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)
    title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})

    canvas = FigureCanvasAgg(f)    
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    f.clear()
    return response
        
@basic_http_auth
def calendar(request, year, month, day):
    
    cal_d = SbCalendar('wlether:archive_day', timezone.now()).formatday(int(year), int(month), int(day))
    cal_m = SbCalendar('wlether:archive_day', timezone.now()).formatmonth(int(year), int(month))
    cal_y = SbCalendar('wlether:archive_day', timezone.now()).formatyear(int(year))
    
    return render(request,'wlether/my_template.html', {'calendar_d': mark_safe(cal_d),
                                                       'calendar_m': mark_safe(cal_m),
                                                       'calendar_y': mark_safe(cal_y),})
  
class ScanTodayArchiveView(TodayArchiveView):
    queryset = Scan.objects.all()
    date_field = "scan_time"
    make_object_list = True
    allow_future = True
    allow_empty = True
    paginate_by = 20
    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))

class ScanDayArchiveView(DayArchiveView):
    queryset = Scan.objects.all()
    date_field = "scan_time"
    make_object_list = True
    allow_future = True
    allow_empty = True
    paginate_by = 20
    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))

class ScanWeekArchiveView(WeekArchiveView):
    queryset = Scan.objects.all()
    date_field = "scan_time"
    make_object_list = True
    allow_future = True
    allow_empty = True
    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))
    
class ScanMonthArchiveView(MonthArchiveView):
    queryset = Scan.objects.all()
    date_field = "scan_time"
    make_object_list = True
    allow_future = True
    allow_empty = True
    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))
    
class ScanYearArchiveView(YearArchiveView):
    queryset = Scan.objects.all()
    date_field = "scan_time"
    make_object_list = True
    allow_future = True
    allow_empty = True
    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))


@basic_http_auth
def index(request):
    latest_scan_list = Scan.objects.order_by('-scan_time')[:60]
    # template = loader.get_template('wlether/index.html') # from django.template import Context, loader
    # context = Context({                                  # .
    #     'latest_scan_list': latest_scan_list,            # .
    # })                                                   # .
    # return HttpResponse(template.render(context))        # .
    context = {'latest_scan_list': latest_scan_list}       # =
    return render(request, 'wlether/index.html', context)

class IndexView(ListView):
    @classmethod
    def as_view(cls, **initkwargs):
        #import pdb; pdb.set_trace()
        return basic_http_auth(super(cls, cls).as_view(**initkwargs))
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context
@basic_http_auth
def detail(request, scan_id):
    # try:                                           # from django.http import Http404
    #     scan = Scan.objects.get(pk=scan_id)        # .
    # except Scan.DoesNotExist:                      # .
    #     raise Http404                              # .
    scan = get_object_or_404(Scan, pk=scan_id)       # =
    return render(request, 'wlether/detail.html', {'scan': scan})
    
@basic_http_auth
def details(request, scan_id, apoint_id):
    apoint = APoint.objects.get(pk=apoint_id)
    # template = loader.get_template('wlether/index.html') # from django.template import Context, loader
    # context = Context({                                  # .
    #     'latest_scan_list': latest_scan_list,            # .
    # })                                                   # .
    # return HttpResponse(template.render(context))        # .
    context = {'scan_id': scan_id, 'apoint': apoint}       # =
    return render(request, 'wlether/details.html', context)

@basic_http_auth
def results(request, scan_id, apoint_id):
    apoint = APoint.objects.get(pk=apoint_id)
    context = {'scan_id': scan_id, 'apoint': apoint}
    return render(request, 'wlether/results.html', context)

# @basic_http_auth
# def calendar(request, year, month):
#     my_workouts = Workouts.objects.order_by('my_date').filter(
#         my_date__year=year, my_date__month=month
#     )
#     my_workouts = [1,2]
#     cal = WorkoutCalendar(my_workouts).formatmonth(year, month)
    
#     return render(request,'wlether/my_template.html', {'calendar': mark_safe(cal),})
  
import json
@basic_http_auth
def collect(request, scan_id, apoint_id):
    if scan_id == '0':
        scan_json = request.body
        scan_dict = json.loads(scan_json)
        scan = Scan()
        update_scan(scan, scan_dict)
    else:
        ap = get_object_or_404(APoint, pk=apoint_id)
        apd = {
            'bssid': request.POST['bssid'],
            'frequency': request.POST['frequency'],
            'signal_level': request.POST['signal_level'],
            'flags': request.POST['flags'],
            'ssid': request.POST['ssid']
            }
        update_apoint(ap, apd)

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('wlether:results',
                                        args=(scan_id, apoint_id,)))

def update_apoint(apoint, apoint_dict):
    apoint.bssid = apoint_dict['bssid']
    apoint.frequency = apoint_dict['frequency']
    apoint.signal_level = apoint_dict['signal_level']
    apoint.flags = apoint_dict['flags']
    apoint.ssid = apoint_dict['ssid']
    apoint.save()
    
def update_scan(scan, scan_dict):
    scan.chassis = scan_dict['chassis']
    scan.adapter = scan_dict['adapter']
    scan.tool = scan_dict['tool']
    scan.time = scan_dict['time']
    #scan.scan_time = timezone.datetime.strptime(scan_dict['time'], '%Y-%m-%d %H:%M:%S %Z')
    scan.scan_time = parse_datetime(scan_dict['time'])
    scan.save()
    
    [update_apoint(scan.apoint_set.create(), ap)
     for ap in scan_dict['aps']]

