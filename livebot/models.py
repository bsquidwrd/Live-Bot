import random
import string
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from cogs.utils.utils import logify_exception_info


class TwitchChannel(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Channel ID')
    name = models.CharField(max_length=255, verbose_name='Channel Name')

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Twitch Channel'
        verbose_name_plural = 'Twitch Channels'


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
    twitch = models.ForeignKey(TwitchChannel, verbose_name='Twitch Channel')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return '{}'.format(self.twitch)

    class Meta:
        verbose_name = 'Twitch Noticication'
        verbose_name_plural = 'Twitch Noticications'


class DiscordServer(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Server ID')
    name = models.CharField(max_length=255, verbose_name='Server Name')

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Discord Server'
        verbose_name_plural = 'Discord Servers'


class DiscordChannel(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Channel ID')
    name = models.CharField(max_length=255, verbose_name='Channel Name')
    server = models.ForeignKey(DiscordServer, verbose_name='Channel Server')

    def __str__(self):
        return '{} - {}'.format(self.server, self.name)

    class Meta:
        verbose_name = 'Discord Channel'
        verbose_name_plural = 'Discord Channels'


class DiscordMessage(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Message ID')
    channel = models.ForeignKey(DiscordChannel)
    timestamp = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    twitch_notification = GenericRelation(TwitchNotification)

    def __str__(self):
        return '[{}] - {}'.format(self.timestamp, self.id)

    class Meta:
        verbose_name = 'Discord Message'
        verbose_name_plural = 'Discord Messages'


class Twitter(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Twitter ID')
    name = models.CharField(max_length=255, verbose_name='Username')

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Twitter Account'
        verbose_name_plural = 'Twitter Accounts'


class Tweet(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Tweet ID')
    twitter = models.ForeignKey(Twitter, verbose_name='Twitter Account')
    message = models.CharField(max_length=140, verbose_name='Tweet Message')
    timestamp = models.DateTimeField(default=timezone.now)
    twitch_notification = GenericRelation(TwitchNotification)

    def __str__(self):
        return '[{}] - {}'.format(self.timestamp, self.message)

    class Meta:
        verbose_name = 'Tweet'
        verbose_name_plural = 'Tweets'


class Notification(models.Model):
    log = models.ForeignKey('Log', verbose_name='Log Item')
    twitch = models.ForeignKey(TwitchChannel, verbose_name='Twitch Channel')
    discord_message = models.ForeignKey(DiscordChannel, verbose_name='Discord Message', blank=True, null=True)
    tweet = models.ForeignKey(Tweet, verbose_name='Twitter Message', blank=True, null=True)

    def __str__(self):
        return '{}'.format(self.twitch)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'


class Log(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    message_token = models.CharField(blank=True, null=True, max_length=50)
    message = models.TextField(default="")
    email = models.BooleanField(default=False)
    subject = models.CharField(max_length=4000, blank=True, null=True, default=None)
    body = models.CharField(max_length=4000, blank=True, null=True, default=None)

    def __str__(self):
        return "[{}] - {}".format(self.timestamp, self.message_token)

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


def random_key(length=50):
    key = ''
    for i in range(length):
        key += random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
    return key
