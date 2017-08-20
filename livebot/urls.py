from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import TemplateView
from .views import *

urlpatterns = [
    url(r'^humans.txt$', TemplateView.as_view(template_name='humans.txt', content_type='text/plain'), name='humans'),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^$', IndexView.as_view(), name='index'),
]
