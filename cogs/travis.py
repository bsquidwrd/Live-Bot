from cogs.utils import logify_exception_info, logify_dict
import asyncio
import discord
import os
import random

import web.wsgi
from livebot.models import *
from django.utils import timezone
from bot import initial_extensions

class Travis:
    """
    Run some internal tests to make sure code works
    """
    def __init__(self, bot):
        self.bot = bot

    async def on_ready(self):
        """
        Bot is loaded
        """
        self.bot.loop.create_task(self.run_tests())

    async def run_tests(self):
        try:
            log_channel = self.bot.get_channel(int(os.environ['LOG_CHANNEL_ID']))
            message_test = None
            message_send_test = False
            message_edit_test = False
            message_delete_test = False

            r = lambda: random.randint(0,255)

            app_info = await self.bot.application_info()
            embed_args = {
                'title': "Test Results",
                'description': "The test results are listed below, each broken out by their own test and corresponding result",
                'colour': discord.Colour.from_rgb(r(), r(), r()),
                'timestamp': timezone.now(),
            }
            embed = discord.Embed(**embed_args)
            embed.set_author(name=app_info.owner.name, icon_url=app_info.owner.avatar_url)
            embed.add_field(name="Colour Value", value=embed_args["colour"], inline=False)

            print("Initial extensions: {}".format(tuple(self.bot.extensions)))
            time_to_wait = 5
            for i in range(0, time_to_wait):
                print("Tasks will be executed in {} seconds".format(time_to_wait-i))
                await asyncio.sleep(1)

            try:
                # Run a test for sending messages
                message_test = await log_channel.send("I was able to send a message during my tests!")
                message_send_test = True
            except Exception as e:
                pass
            embed.add_field(name="Send Message", value=str(message_send_test), inline=True)

            if message_test:
                try:
                    # Run a test for editing messages
                    await message_test.edit(content="I was able to edit a message during my tests!")
                    message_edit_test = True
                except Exception as e:
                    pass
                embed.add_field(name="Edit Message", value=str(message_send_test), inline=True)

                try:
                    # Run a test for deleting messages
                    await message_test.delete()
                    message_delete_test = True
                except Exception as e:
                    pass
                embed.add_field(name="Delete Message", value=str(message_delete_test), inline=True)

            try:
                # Check that Twitch can be reached
                client_id = os.environ['TWITCH_CLIENT_ID']
                headers = {
                    'Client-ID': client_id,
                }
                response = await self.bot.session.get("https://api.twitch.tv/helix/users?login=bsquidwrd", headers=headers)
                embed.add_field(name="Twitch Response", value=response.status, inline=True)
                response_json = await response.json()
                if response_json['data']['profile_image_url'] and response_json['data']['profile_image_url'] != "":
                    embed.set_thumbnail(url=response_json['data']['profile_image_url'])
            except Exception as e:
                print(logify_exception_info(), e)

            await log_channel.send(content="Test Results", embed=embed)
        except Exception as e:
            print(e)
        finally:
            await self.bot.logout()

def setup(bot):
    bot.add_cog(Travis(bot))
