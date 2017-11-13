from discord.ext import commands
from cogs.utils import logify_exception_info, logify_dict, communicate, current_line, log_error, grouper
from dateutil.parser import parse
import asyncio
import discord
import requests
import os
from collections import defaultdict
import importlib

import web.wsgi
from livebot.models import *
from django.db.models import Count
from django.utils import timezone
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
        try:
            importlib.reload(communicate)
        except Exception as e:
            print(e)

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
            while not self.bot.is_ready():
                await asyncio.sleep(1)
            while not self.bot.is_closed():
                await self.run_scheduled_tasks()
                await asyncio.sleep(60)
        except asyncio.CancelledError as e:
            pass

    async def run_scheduled_tasks(self):
        try:
            result = None
            twitch_notifications = defaultdict(list)
            for n in TwitchNotification.objects.all():
                twitch_notifications[n.twitch.name].append(n)

            headers = {
                'Client-ID': self.twitch_app.client_id,
            }

            for notifications in grouper(twitch_notifications, 100):
                stream_names = []
                for v in notifications:
                    # Because it can be None
                    if v:
                        stream_names.append(v)
                channels_appended = ",".join(stream_names)

                result = await self.bot.session.get("https://api.twitch.tv/kraken/streams/?channel={0}".format(channels_appended), headers=headers)
                try:
                    result_json = await result.json()
                except Exception as e:
                    raise Exception("Could not parse JSON from response.")
                if not result.status == 200:
                    log_item = Log.objects.create(message="Could not retrieve list of streams that are being monitored:\n{}".format(logify_dict(result_json)))
                    try:
                        for key in result.headers:
                            value = result.headers[key]
                            log_item.message += "{}: {}\n".format(key, value)
                    except:
                        pass
                    finally:
                        log_item.save()
                    app_info = await self.bot.application_info()
                    error_embed_args = {
                        'title': "Error Running Tasks",
                        'description': "Could not retrieve list of streams that are benig monitored.",
                        'colour': discord.Colour.red(),
                        'timestamp': log_item.timestamp,
                    }
                    author_dict = {
                        'name': self.bot.user.name,
                        'icon_url': app_info.icon_url,
                    }
                    error_dict = {
                        "log token": log_item.message_token,
                    }
                    await log_error(bot=self.bot, content="Could not check for streams that were live. Result is not okay.", d=error_dict, author=author_dict, **error_embed_args)
                    return

                if result_json["_total"] == 0:
                    # No streams live right now, continue on
                    continue

                for stream in result_json['streams']:
                    if stream is not None:
                        if stream['stream_type'] == 'live':
                            twitch = TwitchChannel.objects.get(id=stream['channel']['_id'])
                            timestamp = parse(stream['created_at'])
                            live = TwitchLive.objects.get_or_create(twitch=twitch, timestamp=timestamp)[0]
                            for notification in twitch.twitchnotification_set.all():
                                live_notifications = live.notification_set.filter(live=live, content_type=notification.content_type, object_id=notification.object_id)
                                last_notification = Notification.objects.filter(content_type=notification.content_type, object_id=notification.object_id, live__twitch=twitch, success=True).order_by('-live__timestamp')
                                if live_notifications.filter(success=True).count() >= 1:
                                    continue
                                if live_notifications.filter(success=False).count() == 0:
                                    log = Log.objects.create(message="Attempting to notify for {}\n".format(twitch.name))
                                    live_notification = Notification.objects.create(live=live, content_type=notification.content_type, object_id=notification.object_id, success=False, log=log)
                                else:
                                    live_notification = live_notifications.filter(success=False)[0]

                                if last_notification.count() >= 1:
                                    notification_timedelta = (live_notification.live.timestamp - last_notification[0].live.timestamp)
                                    if notification_timedelta.seconds <= 3600:
                                        live_notification.success = True
                                        live_notification.save()
                                    else:
                                        self.bot.loop.create_task(self.alert(stream, notification, live_notification))
                                else:
                                    self.bot.loop.create_task(self.alert(stream, notification, live_notification))
        except Exception as e:
            log_item = Log.objects.create(message="Could not retrieve list of streams that are being monitored:\n{}\n{}\n".format(logify_exception_info(), e))
            try:
                for key in result.headers:
                    value = result.headers[key]
                    log_item.message += "{}: {}\n".format(key, value)
            except:
                pass
            finally:
                log_item.save()
            app_info = await self.bot.application_info()

            error_embed_args = {
                'title': "Error Running Tasks",
                'description': str(logify_exception_info()),
                'colour': discord.Colour.red(),
                'timestamp': log_item.timestamp,
            }
            author_dict = {
                'name': self.bot.user.name,
                'icon_url': app_info.icon_url,
            }
            error_info = {
                "exception": str(e),
                "message token": log_item.message_token,
            }
            await log_error(bot=self.bot, content="Something went wrong when trying to run through the tasks.", d=error_info, author=author_dict, **error_embed_args)

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
                    if stream['channel']['logo'] and stream['channel']['logo'] != "":
                        embed.set_thumbnail(url=stream['channel']['logo'])
                    game_name = stream['game']
                    if game_name is None or game_name == "":
                        game_name = '[Not Set]'
                    embed.add_field(name="Game", value=game_name, inline=True)
                    embed.add_field(name="Stream", value=twitch.url, inline=True)
                    # embed.set_image(url=stream['preview']['medium'])
                    embed.set_footer(text="Stream start time")
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
