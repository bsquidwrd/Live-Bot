from discord.ext import commands
import asyncio
import traceback
import discord
import inspect
import textwrap
from contextlib import redirect_stdout
import io

# to expose to the eval command
import datetime
from collections import Counter

def get_current_commit():
    """
    Returns the current version the bot is running
    """
    import os
    import subprocess
    git_dir = os.path.join(os.environ['LIVE_BOT_BASE_DIR'], ".git")
    return subprocess.check_output(["git", "--git-dir={}".format(git_dir), "rev-parse", "--verify", "HEAD", "--short"]).decode("utf-8")

class Admin:
    """Admin-only commands that make the bot dynamic."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self.sessions = set()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    def get_syntax_error(self, e):
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command(hidden=True)
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.bot.unload_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command(name='reload', hidden=True)
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
        except Exception as e:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command(name='version', pass_context=True, hidden=True)
    async def version_command(self, ctx):
        """
        Print the version of the bot currently running
        """
        member = ctx.message.server.get_member(self.bot.user.id)
        current_commit = get_current_commit()
        commit_url = member.game.url + '/commit/' + current_commit
        msg = await self.bot.send_message(ctx.message.channel, 'I am currently running on commit `{}`\n\n{}'.format(current_commit, commit_url))

    @commands.command(aliases=['stop'], hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Restarts the bot"""
        await ctx.send(':wave:')
        await self.bot.logout()


def setup(bot):
    bot.add_cog(Admin(bot))
