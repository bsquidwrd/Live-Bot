from discord.ext import commands
from cogs.utils import logify_exception_info, logify_dict, communicate, current_line, log_error, grouper
from cogs.utils.tokens import get_request_headers
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


class Tasks(commands.Cog):
    """
    Runs misc tasks

    bot : Required[obj]
        The bot instance that is currently running
    """
    def __init__(self, bot):
        self.bot = bot
        self._task = bot.loop.create_task(self.run_tasks())
        self.client_id = os.getenv('LIVE_BOT_TWITCH_LIVE', None)
        try:
            importlib.reload(communicate)
        except Exception as e:
            print(e)

    def cog_unload(self):
        self._task.cancel()

    async def on_ready(self):
        """
        Bot is loaded, populate information that is needed for everything
        """
        if not self.client_id:
            print("No Twitch Client ID, unable to run Twitch Tasks")
            self.cog_unload()

    async def run_tasks(self):
        try:
            while not self.bot.is_ready():
                await asyncio.sleep(1)
            while not self.bot.is_closed():
                await self.run_scheduled_tasks()
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def run_scheduled_tasks(self):
        try:
            headers = get_request_headers()
            result = None
            twitch_notifications = defaultdict(list)
            for n in TwitchNotification.objects.all():
                twitch_notifications[n.twitch].append(n)

            for notifications in grouper(twitch_notifications, 75):
                payload = [('type', 'live')]
                # payload = []
                for v in notifications:
                    # Because it can be None
                    if v:
                        payload.append(('user_id', str(v.id)))

                result = await self.bot.session.get("https://api.twitch.tv/helix/streams", headers=headers, params=payload)
                try:
                    result_json = await result.json()
                    # print(result.url)
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
                    error_embed_args = {
                        'title': "Error Running Tasks",
                        'description': "Could not retrieve list of streams that are benig monitored.",
                        'colour': discord.Colour.red(),
                        'timestamp': log_item.timestamp,
                    }
                    author_dict = {
                        'name': self.bot.user.name,
                    }
                    error_dict = {
                        "log token": log_item.message_token,
                    }
                    await log_error(bot=self.bot, content="Could not check for streams that were live. Result is not okay.", d=error_dict, author=author_dict, **error_embed_args)
                    return

                if len(result_json["data"]) == 0:
                    # No streams live right now, continue on
                    continue

                for stream in result_json['data']:
                    if stream is not None:
                        twitch, created = TwitchChannel.objects.get_or_create(id=stream['user_id'])
                        if created:
                            r = await self.bot.session.get("https://api.twitch.tv/helix/users", headers=headers, params={'id': twitch.id})
                            user_json = await r.json()
                            twitch.name = user_json[0]['login']
                            twitch.display_name = user_json[0]['display_name']
                            twitch.profile_image = user_json[0]['profile_image_url']
                            twitch.offline_image = user_json[0]['offline_image_url']
                            twitch.save()
                        timestamp = parse(stream['started_at'])
                        if stream['game_id'] and stream['game_id'] != "":
                            try:
                                game = TwitchGame.objects.get(id=stream['game_id'])
                            except TwitchGame.DoesNotExist:
                                g = await self.bot.session.get("https://api.twitch.tv/helix/games", headers=headers, params={'id': stream['game_id']})
                                game_json = await g.json()
                                try:
                                    game_defaults = {'name': game_json['data'][0]['name'], 'box_art': game_json['data'][0]['box_art_url']}
                                    game = TwitchGame.objects.get_or_create(id=game_json['data'][0]['id'], defaults=game_defaults)[0]
                                except:
                                    game = TwitchGame.objects.get_or_create(id=0, name='[Not Set]')[0]
                        else:
                            game = TwitchGame.objects.get_or_create(id=0, name='[Not Set]')[0]
                        live = TwitchLive.objects.get_or_create(twitch=twitch, timestamp=timestamp, game=game)[0]
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
                                log = live_notification.log

                            if last_notification.count() >= 1:
                                notification_timedelta = (live_notification.live.timestamp - last_notification[0].live.timestamp).total_seconds()
                                if notification_timedelta <= 3600:
                                    log.message += "Stream went live within an hour of their last live instance, marking as success. Timedelta: {}".format(notification_timedelta)
                                    live_notification.success = True
                                    log.save()
                                    live_notification.save()
                                elif notification_timedelta <= notification.delay_minutes*60:
                                    log.message += "Stream went live within {} seconds of their last live instance, marking as success. Timedelta: {}".format(notification.delay_minutes, notification_timedelta)
                                    live_notification.success = True
                                    log.save()
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

            error_embed_args = {
                'title': "Error Running Tasks",
                'description': str(logify_exception_info()),
                'colour': discord.Colour.red(),
                'timestamp': log_item.timestamp,
            }
            author_dict = {
                'name': self.bot.user.name,
            }
            error_info = {
                "exception": str(e),
                "message token": log_item.message_token,
            }
            await log_error(bot=self.bot, content="Something went wrong when trying to run through the tasks.", d=error_info, author=author_dict, **error_embed_args)

    async def alert(self, stream: dict, notification: TwitchNotification, live_notification: Notification):#, game: TwitchGame = TwitchGame(id=0, name='[Not Set]')):
        discord_content_type = DiscordChannel.get_content_type()
        twitter_content_type = Twitter.get_content_type()
        try:
            twitch = notification.twitch
            timestamp = parse(stream['started_at'])
            game = live_notification.live.game
            log = live_notification.log
            message = notification.get_message(name=twitch.display_name, game=game.name)

            if notification.content_type == discord_content_type:
                channel = self.bot.get_channel(int(notification.object_id))
                if channel is None:
                    raise Exception("Bot returned None for Channel ID {}\n".format(notification.object_id))
                else:
                    embed_args = {
                        # 'title': stream['title'],
                        'description': stream['title'],
                        'url': twitch.url,
                        'colour': discord.Colour.dark_purple(),
                        'timestamp': timestamp,
                    }
                    embed = discord.Embed(**embed_args)
                    embed.set_author(name=twitch.display_name)
                    if twitch.profile_image and twitch.profile_image != "":
                        embed.set_thumbnail(url=twitch.profile_image)
                    embed.add_field(name="Game", value=game.name, inline=True)
                    embed.add_field(name="Stream", value=twitch.url, inline=True)
                    # embed.set_image(url=stream['preview']['medium'])
                    embed.set_footer(text="Stream start time")
                    if not live_notification.success:
                        self_member = channel.guild.get_member(self.bot.user.id)
                        # channel_permissions = channel.permissions_for(self_member)
                        # if not channel_permissions.read_messages or not channel_permissions.send_messages or not channel_permissions.embed_links:
                        #     await message.channel.set_permissions(self_member, read_messages=True, send_messages=True, embed_links=True)
                        try:
                            msg = await channel.send("{}".format(message), embed=embed)
                        except Exception as e:
                            raise Exception("Unable to send a message to channel ID {} in guild id {} for stream ID {}\nLine number {}\n{}".format(channel.id, channel.guild.id, twitch.id, current_line(), e))
                        if msg.content == message:
                            log.message += "Notification success\n"
                            live_notification.success = True
                        else:
                            log.message += "Message content did not equal expected content, will try again\n"
                    else:
                        log.message += "Notification already marked as success, skipping\n"

            elif notification.content_type == twitter_content_type:
                twitter = communicate.Twitter(log=log, uid=notification.object_id)
                if not live_notification.success:
                    tweet = twitter.tweet('{} {}'.format(message[:115], twitch.url))
                    if tweet:
                        log.message += "Notification success\n"
                        live_notification.success = True
                    else:
                        log.message += "Tweet not sent, not marking as success and will try again\n"
                else:
                    log.message += "Notification already marked as success, skipping\n"
            else:
                log.message += "Could not determine notification type, assuming success\n"
                live_notification.success = True

        except Exception as e:
            log.message += "Error notifying service:\n{}\n{}\n\n".format(logify_exception_info(), e)

        log.save()
        live_notification.save()


def setup(bot):
    bot.add_cog(Tasks(bot))
