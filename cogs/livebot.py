from discord.ext import commands
from cogs.utils import checks, logify_exception_info, logify_dict, communicate
import asyncio
import discord

import web.wsgi
from livebot.models import *
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from allauth.socialaccount.models import SocialApp


class LiveBot:
    """
    Commands that allow you to start monitoring/unmonitoring a Twitch Channel
    You can also edit the message shown when a streamer goes live
    """
    def __init__(self, bot):
        self.bot = bot

    async def on_ready(self):
        pass

    @commands.group(name="monitor")
    async def monitor_command(self, ctx):
        print("Monitor triggered by {0.author.name}".format(ctx))

    @monitor_command.command(name="stop")
    async def monitor_stop_command(self, ctx, *, action : str):
        await ctx.send("{0.author.mention}: You said to stop {1}".format(ctx, action))


def setup(bot):
    bot.add_cog(LiveBot(bot))
