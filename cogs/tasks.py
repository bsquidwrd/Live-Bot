from discord.ext import commands
from discord.enums import ChannelType
from cogs.utils import checks, config, logify_exception_info, logify_dict, communicate
import asyncio
import discord
import os
import requests
import logging
import urllib
from dateutil.parser import parse

import web.wsgi
from livebot.models import *
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from allauth.socialaccount.models import SocialApp


class Tasks:
    """
    Runs misc tasks

    bot : Required[obj]
        The bot instance that is currently running
    """
    def __init__(self, bot):
        self.bot = bot
        self.twitch_app = SocialApp.objects.get_current('twitch')

    def __unload(self):
        self.task_runner.cancel()

    def populate_info(self):
        """ Populate all users and servers """
        for server in self.bot.servers:
            s = self.get_server(server)
            for channel in server.channels:
                c = self.get_channel(s, channel)

    def get_channel(self, server, channel):
        """
        Returns a :class:`gaming.models.DiscordChannel` object after getting or creating the Channel
        """
        if channel.is_private:
            return False
        else:
            c, created = DiscordChannel.objects.get_or_create(id=channel.id, server=server)
            try:
                c.name = channel.name
                c.save()
            except Exception as e:
                Log.objects.create(message="Error trying to get Channel {} object for server {}.\n{}\n{}".format(c, c.server, logify_exception_info(), e))
            return c

    def get_server(self, server):
        """
        Returns a :class:`gaming.models.DiscordServer` object after getting or creating the server
        """
        error = False
        s, created = DiscordServer.objects.get_or_create(id=server.id)
        try:
            s.name = server.name
            s.save()
        except Exception as e:
            error = True
            Log.objects.create(message="Error trying to get Server object for server {}.\n{}\n{}".format(s, logify_exception_info(), e))
        finally:
            s.save()
            return s

    async def on_ready(self):
        """
        Bot is loaded, populate information that is needed for everything
        """
        if not self.twitch_app:
            print("No Twitch app loaded, unable to run Twitch Tasks")
            self.__unload()
        self.task_runner = self.bot.loop.create_task(self.run_tasks())
        self.populate_info()

    async def run_tasks(self):
        try:
            while not self.bot.is_closed:
                await self.run_scheduled_tasks()
                await asyncio.sleep(15)
        except asyncio.CancelledError as e:
            pass

    async def run_scheduled_tasks(self):
        try:
            result = None
            discord_content_type = DiscordChannel.get_content_type()
            twitter_content_type = Twitter.get_content_type()
            twitch_channels = TwitchChannel.objects.annotate(Count('twitchnotification')).filter(twitchnotification__count__gte=1)

            headers = {
                'Client-ID': self.twitch_app.client_id,
            }

            channels_appended = ",".join([twitch.name for twitch in twitch_channels])

            result = requests.get("https://api.twitch.tv/kraken/streams/?channel={0}".format(channels_appended), headers=headers)
            if not result.ok:
                return

            for stream in result.json()['streams']:
                if stream is not None:
                    if stream['stream_type'] == 'live':
                        twitch = TwitchChannel.objects.get(id=stream['channel']['_id'])
                        timestamp = parse(stream['created_at'])
                        live = TwitchLive.objects.get_or_create(twitch=twitch, timestamp=timestamp)[0]
                        for notification in twitch.twitchnotification_set.all():
                            live_notifications = live.notification_set.filter(live=live, content_type=notification.content_type, object_id=notification.object_id)
                            if live_notifications.filter(success=True).count() >= 1:
                                continue
                            if live_notifications.filter(success=False).count() == 0:
                                log = Log.objects.create(message="Attempting to notify for {}\n".format(twitch.name))
                                live_notification = Notification.objects.create(live=live, content_type=notification.content_type, object_id=notification.object_id, success=False, log=log)
                            else:
                                live_notification = live_notifications.filter(success=False)[0]
                                log = live_notification.log
                            try:
                                message = notification.get_message(name=stream['channel']['display_name'], game=stream['game'])
                                if notification.content_type == discord_content_type:
                                    channel = self.bot.get_channel(str(notification.content_object.id))
                                    if channel is None:
                                        raise Exception("Bot returned None for Channel ID {}\n".format(notification.content_object.id))
                                    else:
                                        embed_args = {
                                            'title': stream['channel']['display_name'],
                                            # 'description': stream['channel']['status'],
                                            'url': twitch.url,
                                            'colour': discord.Colour.dark_purple(),
                                        }
                                        embed = discord.Embed(**embed_args)
                                        embed.set_thumbnail(url=stream['channel']['logo'])
                                        embed.add_field(name="Title", value=stream['channel']['status'], inline=True)
                                        # embed.add_field(name="Game", value=stream['game'], inline=True)
                                        embed.add_field(name="Stream", value=twitch.url, inline=True)
                                        await self.bot.send_message(channel, "{}".format(message), embed=embed)
                                elif notification.content_type == twitter_content_type:
                                    twitter = communicate.Twitter(log=log, uid=notification.object_id)
                                    twitter.tweet('{} {}'.format(message[:115], twitch.url))
                                log.message += "Notification success"
                                live_notification.success = True
                                live_notification.save()
                            except Exception as e:
                                log.message += "Error notifying service:\n{}\n{}".format(logify_exception_info(), e)
                            finally:
                                log.message += "\n\n"
                                log.save()

        except Exception as e:
            print("{}\n{}\n{}".format(logify_exception_info(), e, result))
            pass


def setup(bot):
    bot.add_cog(Tasks(bot))
