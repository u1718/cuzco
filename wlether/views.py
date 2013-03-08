# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
# from django.template import Context, loader
from django.shortcuts import render, get_object_or_404
# from django.http import Http404
from django.core.urlresolvers import reverse
from datetime import datetime

from wlether.models import Scan, APoint

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
                r['WWW-Authenticate'] = 'Basic realm="bat"'
                return r
        r = HttpResponse("Auth Required", status = 401)
        r['WWW-Authenticate'] = 'Basic realm="bat"'
        return r
        
    return wrap

@basic_http_auth
def index(request):
    latest_scan_list = Scan.objects.order_by('-scan_time')[:55]
    # template = loader.get_template('wlether/index.html') # from django.template import Context, loader
    # context = Context({                                  # .
    #     'latest_scan_list': latest_scan_list,            # .
    # })                                                   # .
    # return HttpResponse(template.render(context))        # .
    context = {'latest_scan_list': latest_scan_list}       # =
    return render(request, 'wlether/index.html', context)

@basic_http_auth
def detail(request, scan_id):
    # try:                                           # from django.http import Http404
    #     scan = Scan.objects.get(pk=scan_id)        # .
    # except Scan.DoesNotExist:                      # .
    #     raise Http404                              # .
    scan = get_object_or_404(Scan, pk=scan_id)          # =
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
    return HttpResponse("You're looking at the results of poll %s" % scan_id)

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
            'bssid': request.POST('bssid'),
            'frequency': request.POST('frequency'),
            'signal_level': request.POST('signal_level'),
            'flags': request.POST('flags'),
            'ssid': request.POST('ssid')
            }
        update_apoint(ap, apd)

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse('wlether:results', args=(scan_id, apoint_id,)))

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
    scan.scan_time = datetime.strptime(scan_dict['time'], '%Y-%m-%d %H:%M:%S')
    scan.save()
    
    [update_apoint(scan.apoint_set.create(), ap)
     for ap in scan_dict['aps']]

