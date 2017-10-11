from discord.ext import commands
from .utils import checks, formats
from .utils.paginator import HelpPaginator, CannotPaginate
import discord
from collections import OrderedDict, deque, Counter
import os, datetime
import asyncio
import copy
import unicodedata
import inspect
import requests

import web.wsgi
from livebot.models import Log
from livebot.utils import logify_exception_info

class Meta:
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')
        bot.loop.create_task(self.update_presence())
        self._task = bot.loop.create_task(self.run_tasks())

    def __unload(self):
        self._task.cancel()

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    async def update_presence(self):
        while not self.bot.is_ready():
            await asyncio.sleep(1)
        live_bot_game = discord.Game(name='@me help', url=self.bot.github_url, type=0)
        await self.bot.change_presence(game=live_bot_game, status=discord.Status.online, afk=False)

    @commands.command(name='help')
    async def _help(self, ctx, *, command: str = None):
        """Shows help about a command or the bot"""

        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) or self.bot.get_command(command)

                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except CannotPaginate as e:
            await ctx.send(e)

    @commands.command(hidden=True)
    async def hello(self, ctx):
        """Displays my intro message."""
        app_info = await self.bot.application_info()
        await ctx.send('Hello! I\'m a robot! {0.name}#{0.discriminator} made me.'.format(app_info.owner))

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Displays my full source code or for a specific command.
        To display the source code of a subcommand you can separate it by
        periods, e.g. tag.create for the create subcommand of the tag command
        or by spaces.
        """
        source_url = self.bot.github_url
        if command is None:
            return await ctx.send(source_url)

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        # since we found the command we're looking for, presumably anyway, let's
        # try to access the code itself
        src = obj.callback.__code__
        lines, firstlineno = inspect.getsourcelines(src)
        location = obj.callback.__module__.replace('.', '/') + '.py'

        final_url = f'<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>'
        await ctx.send(final_url)

    @commands.command()
    async def support(self, ctx):
        """
        Shows you how to get help with using me
        """
        invite_url = "https://bots.discord.pw/bots/334870738257444865"
        app_info = await self.bot.application_info()
        me = app_info.owner
        embed_args = {
            "title": "Invite Live Bot:",
            "description": "[Click me!]({})".format(invite_url),
            "colour": 0xD1526A,
        }
        embed = discord.Embed(**embed_args)
        embed.set_author(name = "Live Bot (Discord ID: {})".format(self.bot.user.id), icon_url = self.bot.user.avatar_url)
        embed.add_field(name = "Triggers: ", value = "{} help".format(self.bot.user.mention))
        embed.set_footer(text = "Developer/Owner: {0} (Discord ID: {0.id})".format(me), icon_url = me.avatar_url)
        await ctx.author.send('', embed = embed)
        await ctx.author.send('Support server: https://discord.gg/zXkb4JP')
        await ctx.message.delete()

    async def run_tasks(self):
        try:
            while not self.bot.is_ready():
                await asyncio.sleep(1)
            while not self.bot.is_closed():
                await self.update_avatar()
                await asyncio.sleep(3600)
        except asyncio.CancelledError as e:
            pass

    async def update_avatar(self):
        """
        Update the bot Avatar
        """
        path = os.path.join('avatar.png')
        try:
            os.remove(path)
        except:
            pass
        try:
            app_info = await self.bot.application_info()
            if app_info.icon_url is None or app_info.icon_url == "":
                return
            r = requests.get(app_info.icon_url)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                with open(path, 'rb') as f:
                    await self.bot.user.edit(avatar=f.read())
            else:
                raise Exception("Response code was not ok. Got {0.status_code}".format(r))
        except Exception as e:
            Log.objects.create(message="Avatar could not be updated!\n{0}\n{1}".format(logify_exception_info(), e))
            print(e)

    @commands.command()
    @commands.is_owner()
    async def alert(self, ctx, *, content : str):
        """
        Alerts Guild Owners with a message
        """
        def author_check(m):
            return m.author.id == ctx.author.id

        app_info = await self.bot.application_info()
        embed_args = {
            "title": "Live Bot Notification",
            "description": "{}".format(content),
            "colour": discord.Colour.red(),
            "timestamp": ctx.message.created_at,
        }
        embed = discord.Embed(**embed_args)
        avatar_url = self.bot.user.default_avatar_url if not self.bot.user.avatar else self.bot.user.avatar_url
        embed.set_author(name=ctx.author, url=self.bot.github_url, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        alert_args = {
            "content": f"\N{HEAVY EXCLAMATION MARK SYMBOL} **Message from {app_info.owner}** \N{HEAVY EXCLAMATION MARK SYMBOL}",
            "embed": embed,
        }

        wait_message = await ctx.send(content="{0.author.mention}: Does this look good to you?".format(ctx), embed=embed)
        response_message = await self.bot.wait_for('message', check=author_check, timeout=120)

        try:
            await wait_message.delete()
            await response_message.delete()
        except Exception as e:
            pass

        if response_message.content.lower() == "no":
            await ctx.send("{0.author.mention}: Please run the command again once you are sure you want to send it".format(ctx), delete_after=30.0)
        elif response_message.content.lower() != "yes":
            await ctx.send("{0.author.mention}: I didn't understand your answer.\nPlease run the command and try again.".format(ctx), delete_after=30.0)
        else:
            owners_alerted = []
            for guild in self.bot.guilds:
                if not guild.owner in owners_alerted:
                    try:
                        self.bot.loop.create_task(self.alert_owner(owner=guild.owner, **alert_args))
                        owners_alerted.append(guild.owner)
                    except Exception as e:
                        pass
            await ctx.send("\N{OK HAND SIGN} Message has been sent to {} guild owners.".format(len(owners_alerted)))
            channel = self.bot.get_channel(int(os.environ['LIVE_BOT_ALERT_CHANNEL']))
            await channel.send(**alert_args)
        await ctx.message.delete()

    async def alert_owner(self, owner, **kwargs):
        await owner.send(**kwargs)
        await owner.send(content="Support Server: https://discord.gg/zXkb4JP")


def setup(bot):
    bot.add_cog(Meta(bot))
