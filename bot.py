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
"""

log = logging.getLogger(__name__)

initial_extensions = (
    'cogs.admin',
    'cogs.tasks',
    'cogs.signals',
    'cogs.stats',
    'cogs.meta',
    # 'cogs.livebot',
)

def _prefix_callable(bot, msg):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ', '?livebot ', '!livebot ']
    return base

class LiveBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=_prefix_callable, description=description,
                         pm_help=None, help_attrs=dict(hidden=True))

        self.client_id = int(os.environ['LIVE_BOT_CLIENT_ID'])
        self.client_token = os.environ['LIVE_BOT_TOKEN']
        self.owner_id = int(os.environ['LIVE_BOT_OWNER_ID'])
        self.bots_key = os.environ.get('LIVE_BOT_DBOTS_KEY', None)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.github_url = github_url

        self.add_command(self.do)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send('This command cannot be used in private messages.')
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send('Sorry. This command is disabled and cannot be used.')
        elif isinstance(error, commands.CommandInvokeError):
            print(f'In {ctx.command.qualified_name}:', file=sys.stderr)
            traceback.print_tb(error.original.__traceback__)
            print(f'{error.original.__class__.__name__}: {error.original}', file=sys.stderr)

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = datetime.datetime.utcnow()

        print(f'Ready: {self.user} (ID: {self.user.id})')
        live_bot_game = discord.Game(name='!livebot help', url=github_url, type=0)
        await bot.change_presence(game=live_bot_game, status=discord.Status.online, afk=False)

    async def on_resumed(self):
        print('resumed...')

    async def process_commands(self, message):
        ctx = await self.get_context(message)

        if ctx.command is None:
            return

        destination = None
        if type(message.channel) == discord.abc.PrivateChannel:
            destination = 'Private Message'
        else:
            destination = '#{0.channel.name} ({0.guild.name})'.format(message)
        log_message = '{0.created_at}: {0.author.name} in {1}: {0.content}'.format(message, destination)
        print(log_message)
        log.info(log_message)

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
