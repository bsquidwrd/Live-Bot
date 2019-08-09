from cogs.utils import logify_exception_info, logify_dict
import asyncio
import discord
from discord.ext import commands

import web.wsgi
from livebot.models import *

class UpdateGuilds(commands.Cog):
    """
    Update all Guids, their Channels and ID's within the database
    """
    def __init__(self, bot):
        self.bot = bot


    @commands.is_owner()
    @commands.command(name='populate', hidden=True)
    async def populate_info(self, ctx):
        """ Populate all users and guilds """
        await ctx.send(f"Starting population now... Check console for status updates")
        try:
            deleted_guilds = DiscordGuild.objects.all()
            for guild in self.bot.guilds:
                g = self.get_guild(guild)
                self.bot.log.info(f"Working on guild {g.name} ({g.id})")
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
        finally:
            await ctx.send(f"\N{OK HAND SIGN} All done! {ctx.author.mention}")

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
    bot.add_cog(UpdateGuilds(bot))
