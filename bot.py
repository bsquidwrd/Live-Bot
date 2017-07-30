from discord.ext import commands
import discord
from cogs.utils import checks
import datetime, re
import asyncio
import copy
import logging
import traceback
import sys
import os
from collections import Counter

import web.wsgi
from gaming.models import Log, Channel, Server, DiscordUser, ServerUser
from gaming.utils import logify_exception_info, logify_dict

debug_mode = os.getenv('LIVE_BOT_DEBUG_MODE', 'true')
if not isinstance(debug_mode, bool):
    # LIVE_BOT_DEBUG_MODE can be set to either 'false' or 'no'. Case insensitive
    debug_mode = not (debug_mode.lower() in ['false', 'no'])

github_url = 'https://github.com/bsquidwrd/Live-Bot'

description = """
Hello! I am a bot written by bsquidwrd with a backbone from Danny.
For the nitty gritty, checkout my GitHub: {0}
""".format(github_url)

initial_extensions = [
    'cogs.admin',
    'cogs.tasks',
]

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
bot_start_time = datetime.datetime.utcnow()

logs_dir = os.path.join(os.environ['LIVE_BOT_BASE_DIR'], 'logs', bot_start_time.strftime('%Y'), bot_start_time.strftime('%m'))
os.makedirs(logs_dir, exist_ok=True)
log_filename = '{0}/live_bot.{1}.log'.format(logs_dir, bot_start_time.strftime('%Y-%m-%d.%H-%M-%S'))

handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w')
log.addHandler(handler)
help_attrs = dict(hidden=True)
prefix = ['!livebot ']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None, help_attrs=help_attrs, log=log)

@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)

@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')
    log.info('Logged in as:\nUsername: {0.user.name}\nID: {0.user.id}\n------'.format(bot))
    if not hasattr(bot, 'uptime'):
        bot.uptime = bot_start_time
    live_bot_game = discord.Game(name='!livebot help', url=github_url, type=0)
    await bot.change_presence(game=live_bot_game, status=discord.Status.online, afk=False)

@bot.event
async def on_resumed():
    print('resumed...')

@bot.event
async def on_command(command, ctx):
    bot.commands_used[command.name] += 1
    message = ctx.message
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)
    print('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))
    log.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

@bot.command(pass_context=True, hidden=True)
@checks.is_owner()
async def do(ctx, times : int, *, command):
    """Repeats a command a specified number of times"""
    msg = copy.copy(ctx.message)
    msg.content = command
    for i in range(times):
        await bot.process_commands(msg)

@bot.command(name='git')
async def give_github_url():
    """Gives the URL of the Github repo"""
    await bot.say('You can find out more about me here: {}'.format(github_url))

@bot.command(aliases=['stop'], hidden=True)
@checks.is_owner()
async def restart():
    """Restarts the bot"""
    await bot.say(':wave:')
    await bot.logout()

if __name__ == '__main__':
    if any('debug' in arg.lower() for arg in sys.argv):
        bot.command_prefix = '$'

    bot.client_id = os.environ['LIVE_BOT_CLIENT_ID']
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

    bot.run(os.environ['LIVE_BOT_TOKEN'])
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
