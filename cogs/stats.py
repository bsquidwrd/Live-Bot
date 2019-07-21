from discord.ext import commands
import aiohttp
import json
import logging
import os

global logger
logger = logging.getLogger(__name__)


class Stats(commands.Cog):
    """Cog for updating bot information on misc sites."""
    def __init__(self, bot):
        self.bot = bot
        self._task = self.bot.loop.create_task(self.update_task())


    def cog_unload(self):
        self._task.cancel()

    
    async def update_task(self):
        """This function runs every 30 minutes to automatically update your server count"""
        if not self.bot.debug_mode:
            while not self.bot.is_ready():
                await asyncio.sleep(1)
            while not self.bot.is_closed():
                logger.info('Attempting to post server count')
                try:
                    guild_count = len(self.bot.guilds)
                    await self.update(bot_id=self.bot.user.id, guild_count=guild_count)
                    logger.info('Posted server count')
                except Exception as e:
                    logger.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))
                await asyncio.sleep(1800)

    
    async def update(self, bot_id, guild_count):
        # This is to keep it all under one function
        # so that it can be done in a loop easily
        async with aiohttp.ClientSession() as client:
            await self.update_dbl(client, bot_id, guild_count)


    async def update_dbl(self, client, bot_id, guild_count):
        # DBL - discordbots.org
        token = os.environ.get('DBL_KEY', None)
        if token:
            try:
                BASE_URL = "https://discordbots.org/api"
                headers = {'Authorization': token}
                payload = {'server_count': guild_count}
                url = f'{BASE_URL}/bots/{bot_id}/stats'
                async with client.post(url, data=payload, headers=headers) as resp:
                    logger.info(f'DBL statistics returned {resp.status} for {payload}')
            except Exception as e:
                logger.exception('Failed to post server count to DBL\n{}: {}'.format(type(e).__name__, e))


###########################
# DON'T CHANGE BELOW THIS #
###########################
    async def on_guild_join(self, guild):
        await self.update()

    async def on_guild_remove(self, guild):
        await self.update()

    async def on_ready(self):
        await self.update()

def setup(bot):
    bot.add_cog(Stats(bot))
