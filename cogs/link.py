from discord.ext import commands
from .utils import checks, formats
import discord
import asyncio

import web.wsgi
from livebot.models import Log
from livebot.utils import logify_exception_info

class Link:
    """Commands to link social accounts"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="link")
    @commands.is_owner()
    async def link_command(self, ctx, *, content : str):
        """
        Allows linking of accounts for the website
        """
        app_info = await self.bot.application_info()
        await ctx.send(content="This feature is under development")


def setup(bot):
    bot.add_cog(Link(bot))
