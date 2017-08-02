from django.contrib import admin
from django.apps import apps
from .models import *


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    list_display = ('get_display_name', 'content_type', 'content_object', 'success')
    list_filter = ('content_type',)
    search_fields = ['live__twitch__id', 'live__twitch__name', 'object_id']


@admin.register(TwitchNotification)
class TwitchNotificationAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    list_display = ('get_display_name', 'content_type', 'content_object')
    list_filter = ('content_type',)
    search_fields = ['twitch__id', 'twitch__name', 'object_id']


@admin.register(TwitchLive)
class TwitchLiveAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'

    list_display = ('get_display_name', 'timestamp')
    search_fields = ['twitch__id', 'twitch__name',]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


app = apps.get_app_config('livebot')
for model_name, model in app.models.items():
    if model_name in ['notification', 'twitchnotification', 'twitchlive']:
        continue
    admin.site.register(model)
