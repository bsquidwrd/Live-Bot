from discord.ext import commands
import discord
from cogs.utils import checks
import datetime, re
import json, asyncio
import copy
import logging
import traceback
import aiohttp
import sys
from collections import Counter
import os

import web.wsgi
from cogs.utils.utils import logify_exception_info, logify_dict

debug_mode = os.getenv('LIVE_BOT_DEBUG_MODE', 'true')
if not isinstance(debug_mode, bool):
    # LIVE_BOT_DEBUG_MODE can be set to either 'false' or 'no'. Case insensitive
    debug_mode = not (debug_mode.lower() in ['false', 'no'])

github_url = 'https://github.com/bsquidwrd/Live-Bot'

description = """
Hello! I am a bot written by bsquidwrd with a backbone from Danny.
For the nitty gritty, checkout my GitHub: {0}
""".format(github_url)

description = """
Hello! I am a bot written by Danny to provide some nice utilities.
"""

log = logging.getLogger(__name__)

initial_extensions = (
    'cogs.admin',
    'cogs.tasks',
)

def _prefix_callable(bot, msg):
    user_id = bot.user.id
    base = ['<@!{user_id}> ', '<@{user_id}> ', '?livebot ', '!livebot ']
    return base

class LiveBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=_prefix_callable, description=description,
                         pm_help=None, help_attrs=dict(hidden=True))

        self.client_id = os.environ['LIVE_BOT_CLIENT_ID']
        self.client_token = os.environ['LIVE_BOT_TOKEN']
        self.session = aiohttp.ClientSession(loop=self.loop)

        self.add_command(self.restart)
        self.add_command(self.give_github_url)
        self.add_command(self.do)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print('Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            print('In {ctx.command.qualified_name}:', file=sys.stderr)
            traceback.print_tb(error.original.__traceback__)
            print('{error.original.__class__.__name__}: {error.original}', file=sys.stderr)

    def get_guild_prefixes(self, guild, *, local_inject=_prefix_callable):
        proxy_msg = discord.Object(id=None)
        proxy_msg.guild = guild
        return local_inject(self, proxy_msg)

    async def set_guild_prefixes(self, guild, prefixes):
        if len(prefixes) == 0:
            await self.prefixes.put(guild.id, [])
        elif len(prefixes) > 10:
            raise RuntimeError('Cannot have more than 10 custom prefixes.')
        else:
            await self.prefixes.put(guild.id, sorted(set(prefixes), reverse=True))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print('Ready: {self.user} (ID: {self.user.id})')
        live_bot_game = discord.Game(name='!livebot help', url=github_url, type=0)
        await bot.change_presence(game=live_bot_game, status=discord.Status.online, afk=False)

    async def on_resumed(self):
        print('resumed...')

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_message(self, message):
        if message.author.bot:
            return
        await self.process_commands(message)

    async def close(self):
        await super().close()
        await self.session.close()

    def run(self):
        super().run(self.client_token, reconnect=True)

    @commands.command(name='git')
    async def give_github_url(self, ctx):
        """Gives the URL of the Github repo"""
        await ctx.message.channel.send('You can find out more about me here: {}'.format(github_url))

    @commands.command(aliases=['stop'], hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Restarts the bot"""
        await ctx.message.channel.send(':wave:')
        await self.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def do(self, ctx, times: int, *, command):
        """Repeats a command a specified number of times."""
        msg = copy.copy(ctx.message)
        msg.content = command
        for i in range(times):
            await self.process_commands(msg)


if __name__ == '__main__':
    bot = LiveBot()
    bot.run()
