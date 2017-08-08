from django.contrib import admin
from .models import *


@admin.register(TwitchChannel)
class TwitchChannelAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'
    list_display = ('get_display_name', 'name', 'id')
    search_fields = ['name', 'id']


@admin.register(DiscordServer)
class DiscordServerAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'
    list_display = ('get_display_name', 'name', 'id')
    search_fields = ['name', 'id']


@admin.register(DiscordChannel)
class DiscordChannelAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'
    list_display = ('get_display_name', 'name', 'id', 'server')
    search_fields = ['name', 'id', 'server__id']


@admin.register(Twitter)
class TwitterAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)

    get_display_name.short_description = 'Display Name'
    list_display = ('get_display_name', 'name', 'id')
    search_fields = ['name', 'id']


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
