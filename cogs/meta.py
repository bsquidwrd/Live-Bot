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

class Prefix(commands.Converter):
    async def convert(self, ctx, argument):
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            raise commands.BadArgument('That is a reserved prefix already in use.')
        return argument

class Meta:
    """Commands for utilities related to Discord or the Bot itself."""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    async def on_ready(self):
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

    @commands.command(name='git')
    async def give_github_url(self, ctx):
        """Gives the URL of the Github repo"""
        await ctx.send('You can find out more about me here: {}'.format(self.bot.github_url))

    @commands.command(aliases=['stop'], hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Restarts the bot"""
        await ctx.send(':wave:')
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def change_avatar(self, ctx, *, url : str):
        """
        Update the bot Avatar
        ToDo: Let owner update Avatar
        """
        path = os.path.join(os.environ['LIVE_BOT_BASE_DIR'], 'avatar.png')
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                with open(path, 'rb') as f:
                    await self.bot.user.edit(avatar=f.read())
                    await ctx.send("{0.author.mention}: Avatar updated successfully!".format(ctx))
            else:
                raise Exception("Response code was not ok. Got {0.status_code}".format(r))
        except Exception as e:
            response_message = await ctx.send("{0.author.mention} Avatar could not be updated! The server returned status code {1.status_code}".format(ctx, r))
            print(e)
        finally:
            try:
                os.remove(path)
            except:
                pass


def setup(bot):
    bot.add_cog(Meta(bot))
