from cogs.utils import logify_exception_info, logify_dict
import asyncio
import discord
from discord.ext import commands

import web.wsgi
from livebot.models import *

class Signals(commands.Cog):
    """
    Catches signals and does things with them
    """
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.populate_info())

    async def on_guild_join(self, guild):
        try:
            g = self.get_guild(guild)
            for channel in guild.channels:
                self.get_channel(g, channel)
        except Exception as e:
            print(e)
            Log.objects.create(message="Error adding items when added to guild {}\n{}\n{}".format(g.id, logify_exception_info(), e), email=True)

    async def on_guild_update(self, before, after):
        self.get_guild(after)

    async def on_guild_remove(self, guild):
        try:
            g = self.get_guild(guild)
            channels = DiscordChannel.objects.filter(guild=g)
            for channel in channels:
                TwitchNotification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id=channel.id).delete()
                Notification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id=channel.id).delete()
            channels.delete()
            g.delete()
        except Exception as e:
            print(e)
            Log.objects.create(message="Error removing items when removed from guild {}\n{}\n{}".format(g.id, logify_exception_info(), e), email=True)

    async def on_guild_channel_create(self, channel):
        g = self.get_guild(channel.guild)
        c = self.get_channel(g, channel)

    async def on_guild_channel_delete(self, channel):
        g = self.get_guild(channel.guild)
        c = self.get_channel(g, channel)
        if c:
            TwitchNotification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id=c.id).delete()
            Notification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id=c.id).delete()
            c.delete()

    async def on_guild_channel_update(self, before, after):
        g = self.get_guild(after.guild)
        c = self.get_channel(g, after)

    async def populate_info(self):
        """ Populate all users and guilds """
        while not self.bot.is_ready():
            await asyncio.sleep(1)
        try:
            deleted_guilds = DiscordGuild.objects.all()
            for guild in self.bot.guilds:
                g = self.get_guild(guild)
                deleted_guilds = deleted_guilds.exclude(pk=g.id)
                deleted_channels = DiscordChannel.objects.filter(guild=g)
                for channel in guild.channels:
                    c = self.get_channel(g, channel)
                    deleted_channels = deleted_channels.exclude(id=channel.id)

                TwitchNotification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id__in=[dc.id for dc in deleted_channels]).delete()
                Notification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id__in=[dc.id for dc in deleted_channels]).delete()
                deleted_channels.delete()
            deleted_guilds.delete()
        except Exception as e:
            print(e)

    def get_channel(self, guild, channel):
        """
        Returns a :class:`gaming.models.DiscordChannel` object after getting or creating the Channel
        """
        if type(channel) != discord.channel.TextChannel:
            return
        c, created = DiscordChannel.objects.get_or_create(id=channel.id, guild=guild)
        try:
            c.name = channel.name
            c.save()
        except Exception as e:
            Log.objects.create(message="Error trying to get Channel {} object for guild {}.\n{}\n{}".format(c, c.guild, logify_exception_info(), e))
        finally:
            return c

    def get_guild(self, guild):
        """
        Returns a :class:`gaming.models.DiscordGuild` object after getting or creating the guild
        """
        g, created = DiscordGuild.objects.get_or_create(id=guild.id)
        try:
            g.name = guild.name
            g.save()
        except Exception as e:
            Log.objects.create(message="Error trying to get DiscordGuild object for guild {}.\n{}\n{}".format(g, logify_exception_info(), e))
        finally:
            return g

    async def on_ready(self):
        """
        Bot is loaded
        """
        pass

def setup(bot):
    bot.add_cog(Signals(bot))
