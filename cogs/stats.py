import aiohttp
import json
import logging

log = logging.getLogger(__name__)

DISCORD_BOTS_API = 'https://bots.discord.pw/api'

class Stats:
    """Cog for updating bots.discord.pw bot information."""
    def __init__(self, bot):
        self.bot = bot

    async def update(self):
        if not self.bot.debug_mode:
            guild_count = len(self.bot.guilds)

            payload = json.dumps({
                'server_count': guild_count
            })

            headers = {
                'authorization': self.bot.bots_key,
                'content-type': 'application/json'
            }

            url = f'{DISCORD_BOTS_API}/bots/{self.bot.user.id}/stats'
            async with self.bot.session.post(url, data=payload, headers=headers) as resp:
                log.info(f'DBots statistics returned {resp.status} for {payload}')

    async def on_guild_join(self, guild):
        await self.update()

    async def on_guild_remove(self, guild):
        await self.update()

    async def on_ready(self):
        await self.update()

def setup(bot):
    bot.add_cog(Stats(bot))
