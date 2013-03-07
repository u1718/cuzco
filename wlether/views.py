# Create your views here.
from django.http import HttpResponse
# from django.template import Context, loader
from django.shortcuts import render, get_object_or_404
# from django.http import Http404

from wlether.models import Scan

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

def detail(request, scan_id):
    # try:                                     # from django.http import Http404
    #     scan = Scan.objects.get(pk=scan_id)  # .
    # except Scan.DoesNotExist:                # .
    #     raise Http404                        # .
    scan = get_object_or_404(Scan, pk=scan_id) # =
    return render(request, 'wlether/detail.html', {'scan': scan})

def results(request, poll_id):
    return HttpResponse("You're looking at the results of poll %s." % poll_id)

def vote(request, poll_id):
    return HttpResponse("You're voting on poll %s." % poll_id)
