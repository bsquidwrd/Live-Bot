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


class Tasks:
    """
    Runs misc tasks

    bot : Required[obj]
        The bot instance that is currently running
    """
    def __init__(self, bot):
        self.bot = bot

    def __unload(self):
        self.task_runner.cancel()

    async def on_ready(self):
        """
        Bot is loaaded, populate information that is needed for everything
        """
        self.task_runner = self.bot.loop.create_task(self.run_tasks())

    async def run_tasks(self):
        try:
            while not self.bot.is_closed:
                await self.run_scheduled_tasks()
                await asyncio.sleep(15)
        except asyncio.CancelledError as e:
            pass

    async def run_scheduled_tasks(self):
        try:
            discord_content_type = ContentType.objects.get_for_model(DiscordChannel)
            twitter_content_type = ContentType.objects.get_for_model(Twitter)

            twitch_client_id = os.environ['LIVE_BOT_TWITCH_CLIENT_ID']
            headers = {
                'Client-ID': twitch_client_id,
            }
            twitch_channels = TwitchChannel.objects.annotate(Count('twitchnotification')).filter(twitchnotification__count__gte=1)
            for twitch in twitch_channels:
                result = requests.get("https://api.twitch.tv/kraken/streams/{0}".format(twitch.name), headers=headers).json()
                if result['stream'] is not None:
                    if result['stream']['stream_type'] == 'live':
                        timestamp = parse(result['stream']['created_at'])
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
                                message = notification.get_message(name=result['stream']['channel']['display_name'], game=result['stream']['game'])
                                if notification.content_type == discord_content_type:
                                    channel = self.bot.get_channel(str(notification.content_object.id))
                                    if channel is None:
                                        raise Exception("Bot returned None for Channel ID {}\n".format(notification.content_object.id))
                                    else:
                                        embed_args = {
                                            'title': result['stream']['channel']['display_name'],
                                            'description': result['stream']['channel']['status'],
                                            'url': twitch.url,
                                            'colour': discord.Colour.dark_purple(),
                                        }
                                        embed = discord.Embed(**embed_args)
                                        embed.set_thumbnail(url=result['stream']['channel']['logo'])
                                        embed.add_field(name="Game", value=result['stream']['game'], inline=True)
                                        embed.add_field(name="Stream", value=twitch.url, inline=True)
                                        await self.bot.send_message(channel, message, embed=embed)
                                elif notification.content_type == twitter_content_type:
                                    # twitter = communicate.Twitter(log=log, uid=notification.object_id)
                                    # twitter.tweet('{} {}'.format(message[:115], twitch.url))
                                    pass
                                log.message += "Notification success"
                                live_notification.success = True
                                live_notification.save()
                            except Exception as e:
                                log.message += "Error notifying service:\n{}\n{}".format(logify_exception_info(), e)
                            finally:
                                log.message += "\n\n"
                                log.save()

        except Exception as e:
            print("{}\n{}".format(logify_exception_info(), e))
            pass


def setup(bot):
    bot.add_cog(Tasks(bot))
