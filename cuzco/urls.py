"""cuzco URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView


urlpatterns = [
    url(r'^weather/', include('weather.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url('^accounts/', include('django.contrib.auth.urls', namespace='auth')),
    #url(r'^accounts/', include('django.contrib.auth.urls')),
    #url(r'^accounts/login/$', auth_views.login, {'redirect_authenticated_user': True}),#, 'template_name': 'admin/login.html'}),
    ]
