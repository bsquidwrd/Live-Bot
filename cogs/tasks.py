from discord.ext import commands
from discord.enums import ChannelType
from .utils import checks
import asyncio
import discord


class Tasks:
    """
    Runs misc tasks

    bot : Required[obj]
        The bot instance that is currently running

    - Creates a :class:`gaming.models.Channel` object for every Channel in the Server
    """
    def __init__(self, bot):
        self.bot = bot
        self.task_runner = bot.loop.create_task(self.run_tasks())

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
                await asyncio.sleep(60)
        except asyncio.CancelledError as e:
            pass

    async def run_scheduled_tasks(self):
        print("Task ran!")


def setup(bot):
    bot.add_cog(Tasks(bot))
