import random
import string
from django.db import models
from cogs.utils.utils import logify_exception_info


class DiscordUser(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='User ID')
    name = models.CharField(max_length=255, verbose_name='Username')
    discrimiator = models.CharField(max_length=255, verbose_name='Discrimiator')
    bot = models.BooleanField(default=False, verbose_name='Bot')

    def __str__(self):
        return '{}#{}{}'.format(self.name, self.discrimiator, ' (Bot)' if self.bot else '')

    class Meta:
        verbose_name = 'Discord User'
        verbose_name_plural = 'Discord Users'


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
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Discord Channel'
        verbose_name_plural = 'Discord Channels'


class TwitchChannel(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name='Channel ID')
    name = models.CharField(max_length=255, verbose_name='Channel Name')

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name = 'Twitch Channel'
        verbose_name_plural = 'Twitch Channels'


class Notification(models.Model):
    DISCORD = 'discord'
    TWITTER = 'twitter'
    NOTIFICATION_TYPES = (
        (DISCORD, DISCORD),
        (TWITTER, TWITTER),
    )
    log = models.ForeignKey('Log', verbose_name='Log Item')
    type = models.CharField(choices=NOTIFICATION_TYPES, verbose_name='Notification Type')
    success = models.BooleanField(default=False, verbose_name='Success')

    def __str__(self):
        return '{} {}'.format(self.type, self.log)

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
        return "[%s] - %s" % (self.timestamp, self.message_token)

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
