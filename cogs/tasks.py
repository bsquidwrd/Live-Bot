from discord.ext import commands
from discord.enums import ChannelType
from .utils import checks, config, logify_exception_info
import asyncio
import discord
import os
import requests
import logging


class Tasks:
    """
    Runs misc tasks

    bot : Required[obj]
        The bot instance that is currently running
    """
    def __init__(self, bot):
        self.bot = bot
        self.task_runner = bot.loop.create_task(self.run_tasks())
        self.config = config.Config('config.json', loop=bot.loop)
        self.channels_sent = {}

    def __unload(self):
        self.task_runner.cancel()

    async def on_ready(self):
        """
        Bot is loaaded, populate information that is needed for everything
        """
        pass

    async def run_tasks(self):
        try:
            while not self.bot.is_closed:
                await self.run_scheduled_tasks()
                await asyncio.sleep(10)
        except asyncio.CancelledError as e:
            pass

    async def run_scheduled_tasks(self):
        try:
            twitch_client_id = os.environ['LIVE_BOT_TWITCH_CLIENT_ID']
            channel_name = "rocketleague"
            discord_channel = self.bot.get_channel('225471771355250688')
            server = discord_channel.server
            result = requests.get("https://api.twitch.tv/kraken/streams/{0}?client_id={1}".format(channel_name, twitch_client_id)).json()

            server_identifier = '{}_{}'.format(server.id, channel_name)

            if result['stream'] is not None and not self.channels_sent.get(server_identifier, False):
                await self.bot.send_message(discord_channel, "Channel is live! https://www.twitch.tv/{0}".format(channel_name))
                print("Alerted server '{}' in channel '{}' that stream '{}' is live".format(server.name, discord_channel.name, channel_name))
                self.channels_sent[server_identifier] = True
        except AttributeError as ae:
            pass
        except Exception as e:
            print("{}\n{}".format(logify_exception_info(), e))


def setup(bot):
    bot.add_cog(Tasks(bot))
