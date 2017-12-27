from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from .forms import *
from .models import *


class BaseLiveBotView(View):
    """
    This is the basic view of all the views.
    It requires a login, so all views require a login.
    It also provides basic functionality like saying an error occurred etc
    """
    template_name = 'livebot/index.html'
    app_label = 'home'

    def __init__(self, *args, **kwargs):
        self.context = {}
        self.context['nbar'] = self.app_label
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.context['current_site_domain'] = get_current_site(request).domain
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        messages.add_message(request, messages.ERROR, 'Page not found!')
        return render(request, self.template_name, self.context)


class IndexView(BaseLiveBotView):
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)
