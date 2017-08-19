from django.contrib import admin
from .models import *

class GlobalAdmin(admin.ModelAdmin):
    def get_display_name(self, obj):
        return str(obj)
    get_display_name.short_description = 'Display Name'


@admin.register(TwitchChannel)
class TwitchChannelAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'id')
    search_fields = ['name', 'id']


@admin.register(DiscordGuild)
class DiscordGuildAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'id')
    search_fields = ['name', 'id']


@admin.register(DiscordChannel)
class DiscordChannelAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'id', 'guild')
    search_fields = ['name', 'id', 'guild__id']
    raw_id_fields = ('guild',)
    list_filter = (
        ('guild', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(Twitter)
class TwitterAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'name', 'id')
    search_fields = ['name', 'id']


@admin.register(Notification)
class NotificationAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'content_type', 'content_object', 'success')
    search_fields = ['live__twitch__id', 'live__twitch__name', 'object_id']
    raw_id_fields = ('log', 'live',)
    list_filter = (
        ('success', admin.BooleanFieldListFilter),
        ('content_type', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(TwitchNotification)
class TwitchNotificationAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'content_type', 'content_object')
    search_fields = ['twitch__id', 'twitch__name', 'object_id']
    raw_id_fields = ('twitch',)
    list_filter = (
        ('twitch', admin.RelatedOnlyFieldListFilter),
        ('content_type', admin.RelatedOnlyFieldListFilter),
    )


@admin.register(TwitchLive)
class TwitchLiveAdmin(GlobalAdmin):
    list_display = ('get_display_name', 'timestamp')
    search_fields = ['twitch__id', 'twitch__name',]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(Log)
class LogAdmin(GlobalAdmin):
    date_hierarchy = 'timestamp'
    list_display = ('get_display_name', 'timestamp', 'message_token', 'short_message')
    list_display_links = ('get_display_name',)
    search_fields = ['message_token', 'message']
    ordering = ['-timestamp']
    fieldsets = [
        (None, {'fields': ['timestamp', 'message_token', 'email', 'subject', 'body', 'message']}),
    ]
    readonly_fields = ('timestamp', 'message_token',)
