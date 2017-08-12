from discord.ext import commands
from cogs.utils import logify_exception_info, logify_dict, communicate
from dateutil.parser import parse
import asyncio
import discord
import requests

import web.wsgi
from livebot.models import *
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
        self._task = bot.loop.create_task(self.run_tasks())

    def __unload(self):
        self._task.cancel()

    async def on_ready(self):
        """
        Bot is loaded, populate information that is needed for everything
        """
        if not self.twitch_app:
            print("No Twitch app loaded, unable to run Twitch Tasks")
            self.__unload()

    async def run_tasks(self):
        try:
            while not self.bot.is_closed():
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
                                    channel = self.bot.get_channel(int(notification.content_object.id))
                                    if channel is None:
                                        raise Exception("Bot returned None for Channel ID {}\n".format(notification.content_object.id))
                                    else:
                                        app_info = await self.bot.application_info()
                                        embed_args = {
                                            'title': stream['channel']['display_name'],
                                            'description': stream['channel']['status'],
                                            'url': twitch.url,
                                            'colour': discord.Colour.dark_purple(),
                                        }
                                        embed = discord.Embed(**embed_args)
                                        embed.set_thumbnail(url=stream['channel']['logo'])
                                        embed.add_field(name="Game", value=stream['game'], inline=True)
                                        # embed.add_field(name="Game", value=stream['game'], inline=True)
                                        embed.add_field(name="Stream", value=twitch.url, inline=True)
                                        # embed.set_image(url=stream['preview']['medium'])
                                        embed.set_footer(text=log.message_token)
                                        await channel.send("{}".format(message), embed=embed)
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
