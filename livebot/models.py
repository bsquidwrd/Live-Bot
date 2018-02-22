import random
import string
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from cogs.utils import logify_exception_info

class TwitchGame(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name='Game ID')
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Game Name')
    box_art = models.URLField(blank=True, null=True, verbose_name="Game Box Art")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Twitch Game"
        verbose_name_plural = "Twitch Games"


class TwitchChannel(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name='Channel ID')
    name = models.CharField(max_length=255, verbose_name='Channel Name')
    display_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Channel Display Name')
    profile_image = models.URLField(blank=True, null=True, verbose_name="Profile Image URL")
    offline_image = models.URLField(blank=True, null=True, verbose_name="Offline Image URL")

    def __str__(self):
        if self.display_name is None or self.display_name == "":
            return str(self.name)
        else:
            return str(self.display_name)

    @property
    def url(self):
        return 'https://twitch.tv/{}'.format(self.name)

    class Meta:
        verbose_name = 'Twitch Channel'
        verbose_name_plural = 'Twitch Channels'
        ordering = ['name']


class DiscordGuild(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name='Guild ID')
    name = models.CharField(max_length=255, verbose_name='Guild Name')

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Discord Guild'
        verbose_name_plural = 'Discord Guilds'
        ordering = ['name']


class DiscordChannel(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name='Channel ID')
    name = models.CharField(max_length=255, verbose_name='Channel Name')
    guild = models.ForeignKey(DiscordGuild, verbose_name='Channel Guild', on_delete=models.CASCADE)

    def __str__(self):
        return '{}'.format(self.name)

    @classmethod
    def get_content_type(cls):
        return ContentType.objects.get_for_model(cls)

    class Meta:
        verbose_name = 'Discord Channel'
        verbose_name_plural = 'Discord Channels'
        ordering = ['guild__name', 'name']


class Twitter(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name='Twitter ID')
    name = models.CharField(max_length=255, verbose_name='Username')

    def __str__(self):
        return '{}'.format(self.name)

    @classmethod
    def get_content_type(cls):
        return ContentType.objects.get_for_model(cls)

    class Meta:
        verbose_name = 'Twitter Account'
        verbose_name_plural = 'Twitter Accounts'
        ordering = ['name']


class TwitchNotification(models.Model):
    """
    content_type = Model Type
    object_id = PK for content_type
    content_object = Reference to actual model with content

    Examples:
        - TwitchNotification.objects.create(twitch=TwitchChannel, content_object=DiscordMessage)
        - TwitchNotification.objects.create(twitch=TwitchChannel, content_object=Tweet)
        - TwitchNotification.objects.filter(twitch=TwitchChannel, content_type=ContentType.objects.get_for_model(DiscordMessage), object_id=DiscordMessage.pk)
        - TwitchNotification.objects.get(twitch=TwitchChannel, content_type=ContentType.objects.get_for_model(DiscordMessage), object_id=DiscordMessage.pk)

    This is meant to be used to store related information sent for
    Twitter, Discord or anything added in the future.

    This is where users will store what DiscordChannel or Twitter or
    anything else they want notified when they go live
    """
    twitch = models.ForeignKey(TwitchChannel, verbose_name='Twitch Channel', on_delete=models.CASCADE)
    limit = models.Q(app_label = 'livebot')
    content_type = models.ForeignKey(ContentType, limit_choices_to=limit, on_delete=models.CASCADE)
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    message = models.CharField(max_length=255, verbose_name='Notification Message')

    def __str__(self):
        return '{}'.format(self.twitch)

    def save(self, *args, **kwargs):
        # if self.message == "" or self.message is None:
        #     if self.content_type == DiscordChannel.get_content_type():
        #         self.message = "{name} is live and is playing {game}! {url}"
        #     elif self.content_type == Twitter.get_content_type():
        #         self.message = "I'm live and playing {game}! {url}"
        #     else:
        #         self.message = "{name} is live! {url}"
        super().save(*args, **kwargs)

    def get_message(self, *args, **kwargs):
        # Used to determine type of post to be made and to post about it
        message_dict = {
            'url': self.twitch.url,
        }
        message = self.message.format(**message_dict, **kwargs)
        return message

    class Meta:
        verbose_name = 'Twitch Notification'
        verbose_name_plural = 'Twitch Notifications'


class TwitchLive(models.Model):
    twitch = models.ForeignKey(TwitchChannel, verbose_name='Twitch Channel', on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    def __str__(self):
        return '{}'.format(self.twitch)

    class Meta:
        verbose_name = 'Twitch Live'
        verbose_name_plural = 'Twitch Live Instances'
        ordering = ['-timestamp', 'twitch__name']


class Notification(models.Model):
    """
    content_type = Model Type
    object_id = PK for content_type
    content_object = Reference to actual model with content

    Examples:
        - Notification.objects.create(live=TwitchLive, content_object=DiscordMessage)
        - Notification.objects.create(live=TwitchLive, content_object=Tweet)
        - Notification.objects.filter(live=TwitchLive, content_type=ContentType.objects.get_for_model(DiscordMessage), object_id=DiscordMessage.pk)
        - Notification.objects.get(live=TwitchLive, content_type=ContentType.objects.get_for_model(DiscordMessage), object_id=DiscordMessage.pk)

    This is meant to be the area to store notification results (whether success or not) when they go live
    """
    log = models.ForeignKey('Log', verbose_name='Log Item', on_delete=models.CASCADE)
    live = models.ForeignKey(TwitchLive, verbose_name='Twitch Live', on_delete=models.CASCADE)
    limit = models.Q(app_label = 'livebot')
    content_type = models.ForeignKey(ContentType, limit_choices_to=limit, on_delete=models.CASCADE)
    object_id = models.BigIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    success = models.BooleanField(default=False, verbose_name='Success')

    def __str__(self):
        return '{}'.format(self.live)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-live__timestamp']


class Log(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    message_token = models.CharField(blank=True, null=True, max_length=50)
    message = models.TextField(default="")
    email = models.BooleanField(default=False)
    subject = models.CharField(max_length=4000, blank=True, null=True, default=None)
    body = models.CharField(max_length=4000, blank=True, null=True, default=None)

    def __str__(self):
        return "[{}] - {}".format(self.timestamp, self.message_token)

    def save(self, *args, **kwargs):
        self.generate_log_token(save=False)
        super().save(*args, **kwargs)

    @property
    def short_message(self):
        from django.template.defaultfilters import truncatechars
        return truncatechars(self.message, 100)

    def generate_log_token(self, save=True):
        try:
            if self.message_token is None or self.message_token == '':
                self.message_token = self.generate_token()
                if save:
                    self.save()
            return True
        except Exception as e:
            print(e)
            self.__class__.objects.create(message="{}\nError generating log token.\n\nException:\n{}".format(logify_exception_info(), e), message_token="ERROR_GENERATING_LOG_TOKEN")
            return False

    def random_key(self, length=50):
        key = ''
        for i in range(length):
            key += random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        return key

    def generate_token(self):
        token_key = random_key()
        if self.__class__.objects.filter(message_token=token_key).count() >= 1:
            token_key = self.generate_token()
        return token_key

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Logs'
        ordering = ['-timestamp']


def random_key(length=50):
    key = ''
    for i in range(length):
        key += random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
    return key

import livebot.signals
