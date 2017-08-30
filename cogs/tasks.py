from discord.ext import commands
from cogs.utils import logify_exception_info, logify_dict, communicate, current_line
from dateutil.parser import parse
import asyncio
import discord
import requests

import web.wsgi
from web import environment
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
                await asyncio.sleep(60)
        except asyncio.CancelledError as e:
            pass

    async def run_scheduled_tasks(self):
        try:
            log_channel = self.bot.get_channel(environment.LOG_CHANNEL_ID)
            result = None
            twitch_channels = TwitchChannel.objects.annotate(Count('twitchnotification')).filter(twitchnotification__count__gte=1)

            headers = {
                'Client-ID': self.twitch_app.client_id,
            }

            channels_appended = ",".join([twitch.name for twitch in twitch_channels])

            result = requests.get("https://api.twitch.tv/kraken/streams/?channel={0}".format(channels_appended), headers=headers)
            result_json = result.json()
            if not result.ok:
                log_item = Log.objects.create(message="Could not retrieve list of streams that are being monitored:\n{}".format(result.text))
                app_info = await self.bot.application_info()
                error_embed_args = {
                    'title': "Error Running Tasks",
                    'description': "Could not retrieve list of streams that are benig monitored.",
                    'colour': discord.Colour.red(),
                    'timestamp': log_item.timestamp,
                }
                error_embed = discord.Embed(**error_embed_args)
                error_embed.set_author(name=self.bot.user.name, icon_url=app_info.icon_url)
                error_embed.add_field(name="Error", value=result_json["error"], inline=True)
                error_embed.add_field(name="Status Code", value=result_json["status"], inline=True)
                error_embed.add_field(name="Message", value=result_json["message"], inline=False)
                error_embed.add_field(name="Message Token", value=log_item.message_token, inline=False)
                await log_channel.send(content="Could not check for streams that were live. Result is not okay.", embed=error_embed)
                return

            if result_json["_total"] == 0:
                # No streams live right now, continue on
                return

            for stream in result_json['streams']:
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
                            self.bot.loop.create_task(self.alert(stream, notification, live_notification))
        except Exception as e:
            print("{}\n{}\n{}".format(logify_exception_info(), e, result))
            log_item = Log.objects.create(message="Could not retrieve list of streams that are being monitored:\n{}\n{}".format(logify_exception_info(), e))
            app_info = await self.bot.application_info()
            error_embed_args = {
                'title': "Error Running Tasks",
                'description': str(logify_exception_info()),
                'colour': discord.Colour.red(),
                'timestamp': log_item.timestamp,
            }
            error_embed = discord.Embed(**error_embed_args)
            error_embed.set_author(name=self.bot.user.name, icon_url=app_info.icon_url)
            error_embed.add_field(name="Exception", value=str(e), inline=False)
            error_embed.add_field(name="Message Token", value=log_item.message_token, inline=False)
            await log_channel.send(content="Something went wrong when trying to run through the tasks.", embed=error_embed)

    async def alert(self, stream, notification, live_notification):
        discord_content_type = DiscordChannel.get_content_type()
        twitter_content_type = Twitter.get_content_type()
        try:
            twitch = notification.twitch
            timestamp = parse(stream['created_at'])
            log = live_notification.log
            message = notification.get_message(name=stream['channel']['display_name'], game=stream['game'])

            if notification.content_type == discord_content_type:
                channel = self.bot.get_channel(int(notification.object_id))
                if channel is None:
                    raise Exception("Bot returned None for Channel ID {}\n".format(notification.object_id))
                else:
                    app_info = await self.bot.application_info()
                    embed_args = {
                        # 'title': stream['channel']['display_name'],
                        'description': stream['channel']['status'],
                        'url': twitch.url,
                        'colour': discord.Colour.dark_purple(),
                        'timestamp': timestamp,
                    }
                    embed = discord.Embed(**embed_args)
                    embed.set_author(name=stream['channel']['display_name'], icon_url=app_info.icon_url)
                    embed.set_thumbnail(url=stream['channel']['logo'])
                    game_name = stream['game']
                    if game_name is None:
                        game_name = '[Not Set]'
                    embed.add_field(name="Game", value=game_name, inline=True)
                    embed.add_field(name="Stream", value=twitch.url, inline=True)
                    # embed.set_image(url=stream['preview']['medium'])
                    embed.set_footer(text="ID: {} | Stream start time".format(twitch.id))
                    if not live_notification.success:
                        try:
                            await channel.send("{}".format(message), embed=embed)
                        except Exception as e:
                            raise Exception("Unable to send a message to channel ID {} in guild id {} for stream ID {}\nLine number {}\n{}".format(channel.id, channel.guild.id, twitch.id, current_line(), e))

            elif notification.content_type == twitter_content_type:
                twitter = communicate.Twitter(log=log, uid=notification.object_id)
                if not live_notification.success:
                    twitter.tweet('{} {}'.format(message[:115], twitch.url))
            log.message += "Notification success"
            live_notification.success = True
            live_notification.save()

        except Exception as e:
            log.message += "Error notifying service:\n{}\n{}".format(logify_exception_info(), e)
        finally:
            log.message += "\n\n"
            log.save()


def setup(bot):
    bot.add_cog(Tasks(bot))
