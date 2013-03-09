# This file contains the WSGI configuration required to serve up your
# web application at http://u1718.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Django project

import os
import sys

## add your project directory to the sys.path
#project_home = u'/home/u1718/cuzco'
#if project_home not in sys.path:
#sys.path.append(project_home)

# set environment variable to tell django where your settings.py is
os.environ['DJANGO_SETTINGS_MODULE'] = 'cuzco.settings'

# serve django via WSGI
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

from twisted.web import server
from twisted.web.wsgi import WSGIResource
from twisted.python.threadpool import ThreadPool
from twisted.internet import reactor
from twisted.application import service, strports

# Create and start a thread pool,
wsgiThreadPool = ThreadPool()
wsgiThreadPool.start()

# ensuring that it will be stopped when the reactor shuts down
reactor.addSystemEventTrigger('after', 'shutdown', wsgiThreadPool.stop)

# def application(environ, start_response):
#     """A basic WSGI application"""
#     start_response('200 OK', [('Content-type','text/plain')])
#     return ['Hello World!']

# Create the WSGI resource
wsgiAppAsResource = WSGIResource(reactor, wsgiThreadPool, application)


# Hooks for twistd
application = service.Application('Cuzco')
server = strports.service('tcp:'+os.environ['PORT'], server.Site(wsgiAppAsResource))
server.setServiceParent(application)
