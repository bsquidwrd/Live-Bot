from discord.ext import commands
from cogs.utils import logify_exception_info, logify_dict, current_line, log_error, grouper
import asyncio
import discord
import requests
import os

import web.wsgi
from livebot.models import BearerToken, Log
from allauth.socialaccount.models import SocialApp


class Token(commands.Cog):
    """
    Runs bearer token refresh tasks

    bot : Required[obj]
        The bot instance that is currently running
    """

    def __init__(self, bot):
        self.bot = bot
        self._task = bot.loop.create_task(self.run_tasks())
        self.social_app = SocialApp.objects.get(client_id=os.getenv('LIVE_BOT_TWITCH_LIVE', None))

    def cog_unload(self):
        self._task.cancel()

    async def on_ready(self):
        """
        Bot is loaded, populate information that is needed for everything
        """
        if not self.social_app:
            print("No Social App found, unable to run Bearer Token Tasks")
            self.cog_unload()

    async def run_tasks(self):
        try:
            while not self.bot.is_ready():
                await asyncio.sleep(1)
            while not self.bot.is_closed():
                time_to_wait = await self.run_scheduled_tasks()
                await asyncio.sleep(time_to_wait)
        except asyncio.CancelledError:
            pass

    async def run_scheduled_tasks(self):
        result = None

        bearer_tokens = BearerToken.objects.filter(expired=False)

        if bearer_tokens.count() == 0:
            return 60
        elif bearer_tokens.count() > 1:
            Log.objects.create(message='More than one Bearer Token found that is not expired', email=True)
            bearer_tokens.update(expired=True)
            self.cog_unload()
            return 1800 # 30 minutes

        bearer_token = bearer_tokens[0]

        payload = {
            'client_id': self.social_app.client_id,
            'client_secret': self.social_app.secret,
            'grant_type': 'refresh_token',
            'refresh_token': bearer_token.refresh_token,
        }

        result = await self.bot.session.post("https://id.twitch.tv/oauth2/token", params=payload)
        try:
            result_json = await result.json()
        except Exception as e:
            raise Exception("Could not parse JSON from response.")
        if result.status == 401:
            Log.objects.create(message='Token refresh failed: {}\n{}'.format(bearer_token.access_token, logify_dict(result_json)), email=True)
            return 1800 # 30 minutes
        elif not result.status == 200:
            log_item = Log.objects.create(
                message="Could not retrieve new Bearer Token:\n{}".format(logify_dict(result_json)))
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
                'description': "Could not retrieve new Bearer Token",
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
            return 60

        try:
            bearer_token.expired = True
            bearer_token.save()

            new_bearer_token = BearerToken.objects.create(
                access_token=result_json['access_token'],
                expires_in=result_json.get('expires_in', 3600),
                refresh_token=result_json['refresh_token']
            )
            return new_bearer_token.expires_in

        except Exception as e:
            Log.objects.create(message='{}\nBearer Token unable to be udpated\n{}'.format(logify_exception_info(), e), email=True)
            if bearer_token.expired:
                bearer_token.expired = False
                bearer_token.save()
                try:
                    new_bearer_token.delete()
                except BearerToken.DoesNotExist:
                    pass
            return 60


def setup(bot):
    bot.add_cog(Token(bot))
