from discord.ext import commands
from cogs.utils import checks, logify_exception_info, logify_dict, communicate
import asyncio
import discord
import requests
import copy

import web.wsgi
from livebot.models import *
from allauth.socialaccount.models import SocialApp
from livebot.utils import logify_dict, logify_exception_info

QUESTION_TIMEOUT = 120.0

class UserCancelled(Exception):
    pass

class LiveBot:
    """
    Commands that allow you to start monitoring/unmonitoring a Twitch Channel
    You can also edit the message shown when a streamer goes live
    """
    def __init__(self, bot):
        self.bot = bot
        self.author = None
        self.TWITCH_USER_URL = "https://api.twitch.tv/kraken/users/{username}"

    async def on_ready(self):
        pass

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            # await ctx.send(error)
            Log.objects.create(message="Error running command: {0.command}\n{1}".format(ctx, error))

    @commands.group(name="monitor")
    @checks.is_mod()
    async def monitor_command(self, ctx):
        """
        The base command to all the functions I perform.
        See the help page for this command to learn more.
        """
        if ctx.invoked_subcommand is None:
            msg = copy.copy(ctx.message)
            msg.content = "{} help monitor".format(self.bot.user.mention)
            await self.bot.process_commands(msg)

    @monitor_command.command(aliases=["edit"], name="add")
    async def monitor_add_command(self, ctx):
        """
        Start monitoring a channel for when they go live
        """
        def author_check(m):
            return m.author.id == ctx.author.id

        try:
            wait_message_args = {
                'description': "What stream should I monitor for this server?",
                'colour': discord.Colour.dark_purple(),
            }
            wait_message_embed = discord.Embed(**wait_message_args)
            wait_message_embed.set_footer(text="Example: bsquidwrd")
            wait_message = await ctx.send("{0.author.mention}".format(ctx), embed=wait_message_embed)
            response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

            twitch_app = SocialApp.objects.get_current('twitch')
            headers = {
                'Client-ID': twitch_app.client_id,
            }
            result = requests.get(url=self.TWITCH_USER_URL.format(username=response_message.clean_content), headers=headers)
            if result.status_code == requests.codes.ok:
                result = result.json()
                twitch_channel = TwitchChannel.objects.get_or_create(id=result['_id'])[0]
                try:
                    # Update twitch channel name, just in case it's different in my database
                    twitch_channel.name = result['name']
                    twitch_channel.save()
                except:
                    pass
                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass

                wait_message_args = {
                    'title': result['display_name'],
                    'description': result['bio'],
                    'url': "https://twitch.tv/{}".format(result['name']),
                    'colour': discord.Colour.dark_purple(),
                }
                wait_message_embed = discord.Embed(**wait_message_args)
                if result['logo']:
                    wait_message_embed.set_thumbnail(url=result['logo'])
                wait_message_embed.add_field(name="Stream", value=twitch_channel.url, inline=True)
                wait_message_embed.set_footer(text="Please type YES or NO")
                wait_message = await ctx.send(content="{0.author.mention}: Is this the channel you're looking for?".format(ctx), embed=wait_message_embed)
                response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

                if response_message.content.lower() == "no":
                    await ctx.send("{0.author.mention}: Looks like I couldn't find what you're looking for.\nPlease run the command again once you are sure the name is right".format(ctx), delete_after=30.0)
                    raise UserCancelled
                elif response_message.content.lower() != "yes":
                    await ctx.send("{0.author.mention}: I didn't understand your answer.\nPlease run the command and try again.".format(ctx), delete_after=30.0)
                    raise UserCancelled
                else:
                    # User typed yes, continue on
                    pass

                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass

                # Ask the user what the message should be and if it should mention everyone
                char_count = 0
                mention_everyone = True
                wait_message_args = {
                    'description': "Should the alert message mention everyone?",
                    'colour': discord.Colour.dark_purple(),
                }
                wait_message_embed = discord.Embed(**wait_message_args)
                wait_message_embed.set_footer(text="Please type YES or NO")
                wait_message = await ctx.send(content="{0.author.mention}".format(ctx), embed=wait_message_embed)
                response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

                if response_message.content.lower() == "no":
                    mention_everyone = False
                elif response_message.content.lower() != "yes":
                    await ctx.send("{0.author.mention}: I didn't understand your answer.\nPlease run the command and try again.".format(ctx), delete_after=30.0)
                    raise UserCancelled
                else:
                    # User typed yes, continue on
                    char_count += len("@everyone ")

                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass

                # Ask user for message here
                parameters_message = "{name} - Streamers name\n"
                parameters_message += "{game} - Game they are playing\n"
                parameters_message += "{url} - URL to their stream\n"
                wait_message_args = {
                    'description': "What message should be sent? (Max 255 characters)\nIf you'd like to use the default (see footer) type `default`",
                    'colour': discord.Colour.dark_purple(),
                }
                wait_message_embed = discord.Embed(**wait_message_args)
                wait_message_embed.add_field(name="Parameters", value=parameters_message, inline=True)
                wait_message_embed.set_footer(text="Default: {name} is live and is playing {game}! {url}")
                wait_message = await ctx.send(content="{0.author.mention}".format(ctx), embed=wait_message_embed)
                response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

                if response_message.content.lower() == "default":
                    message_for_notification = "{name} is live and is playing {game}! {url}"
                elif len(response_message.clean_content) + char_count > 255:
                    await ctx.send("{0.author.mention}: The message you type was too long. Please type run the command again with a shorter message".format(ctx), delete_after=30.0)
                    raise UserCancelled
                else:
                    message_for_notification = response_message.clean_content

                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass

                # User chose the right channel, now let's ask which channel they want to use
                wait_message_args = {
                    'description': "Which channel(s) should I notify when **{0.name}** goes live?".format(twitch_channel),
                    'colour': discord.Colour.dark_purple(),
                }
                wait_message_embed = discord.Embed(**wait_message_args)
                wait_message_embed.set_footer(text="Please mention the channel(s) with the # prefix")
                wait_message = await ctx.send(content="{0.author.mention}".format(ctx), embed=wait_message_embed)
                response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

                if (response_message.channel_mentions) == 0:
                    await ctx.send("{0.author.mention}: Looks like you didn't mention any channels to be notified. Please run the command again.".format(ctx), delete_after=30.0)
                    raise UserCancelled
                else:
                    # User mentioned channels
                    added_channels = []
                    discord_guild = DiscordGuild.objects.get_or_create(id=ctx.guild.id)[0]
                    try:
                        discord_guild.name = ctx.guild.name
                        discord_guild.save()
                    except:
                        pass

                    for channel in response_message.channel_mentions:
                        discord_channel = DiscordChannel.objects.get_or_create(id=channel.id, guild=discord_guild)[0]
                        try:
                            discord_channel.name = channel.name
                            discord_channel.save()
                        except:
                            pass

                        try:
                            notification_args = {
                                "twitch": twitch_channel,
                                "content_type": DiscordChannel.get_content_type(),
                                "object_id": discord_channel.id,
                            }
                            twitch_notification = TwitchNotification.objects.get_or_create(**notification_args)[0]
                            try:
                                twitch_notification.message = "{}{}".format("@everyone " if mention_everyone else "", message_for_notification)
                                twitch_notification.save()
                            except:
                                pass
                            added_channels.append(discord_channel)
                        except:
                            continue

                    added_channels_message = ", ".join([c.name for c in added_channels])

                    embed_args = {
                        'description': "I will monitor for when **{0.name}** goes live!".format(twitch_channel),
                        'colour': discord.Colour.dark_purple(),
                    }
                    embed = discord.Embed(**embed_args)
                    embed.set_thumbnail(url=result['logo'])
                    embed.add_field(name="Notify everyone?", value=str(mention_everyone), inline=True)
                    embed.add_field(name="Message", value=message_for_notification, inline=True)
                    embed.add_field(name="Channels", value=added_channels_message, inline=False)
                    app_info = await self.bot.application_info()
                    avatar = app_info.owner.default_avatar_url if not app_info.owner.avatar else app_info.owner.avatar_url
                    embed.set_footer(text = "Developer/Owner: {0.name}#{0.discriminator} (Shard ID: {1})".format(app_info.owner, ctx.guild.shard_id), icon_url = avatar)
                    await ctx.send("{0.author.mention}".format(ctx), embed=embed, delete_after=60.0)

            else:
                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass
                raise Exception("Result status was not okay: \n{}".format(result.text))

        except asyncio.TimeoutError as te:
            await ctx.send("{} It looks like you took too long to respond. Please run the command again if you wish to continue.".format(ctx.author.mention))
            waiting_for_twitch_name = False
            error_occurred = True

        except UserCancelled as uc:
            # User cancelled option or something wasn't understood
            pass

        except Exception as e:
            Log.objects.create(message="Error running add command for {0.author.id} {0.author.name}\n{1}\n{2}".format(ctx, logify_exception_info(), e))
            try:
                await ctx.send("{}, Looks like an error ocurred. Please try again.\nIf the issue persists, please alert my owner.".format(ctx.author.mention))
            except:
                pass

        try:
            await ctx.message.delete()
            await wait_message.delete()
            await response_message.delete()
        except:
            pass

    @monitor_command.command(name="stop")
    async def monitor_stop_command(self, ctx):
        """
        Stop monitoring a channel for when they go live
        """
        def author_check(m):
            return m.author.id == ctx.author.id

        try:
            twitch_notifications = TwitchNotification.objects.filter(content_type=DiscordChannel.get_content_type(), object_id__in=[d.id for d in DiscordChannel.objects.filter(guild__id=ctx.guild.id)])
            wait_message_args = {
                'description': "What stream should I stop monitoring for this server?",
                'colour': discord.Colour.dark_purple(),
            }
            wait_message_embed = discord.Embed(**wait_message_args)
            wait_message_embed.add_field(name="Channels", value=", ".join([tn.twitch.name for tn in twitch_notifications]), inline=False)
            wait_message_embed.set_footer(text="Example: bsquidwrd")
            wait_message = await ctx.send("{0.author.mention}".format(ctx), embed=wait_message_embed)
            response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

            try:
                await wait_message.delete()
                await response_message.delete()
            except:
                pass

            twitch_channel = TwitchChannel.objects.get(name=response_message.clean_content)
            twitch_notifications = twitch_notifications.filter(twitch=twitch_channel)
            twitch_app = SocialApp.objects.get_current('twitch')
            headers = {
                'Client-ID': twitch_app.client_id,
            }
            result = requests.get(url=self.TWITCH_USER_URL.format(username=response_message.clean_content), headers=headers)
            if result.status_code == requests.codes.ok:
                result = result.json()
                wait_message_args = {
                    'title': result['display_name'],
                    'description': result['bio'],
                    'url': "https://twitch.tv/{}".format(result['name']),
                    'colour': discord.Colour.dark_purple(),
                }
                wait_message_embed = discord.Embed(**wait_message_args)
                wait_message_embed.set_thumbnail(url=result['logo'])
                wait_message_embed.add_field(name="Stream", value=twitch_channel.url, inline=True)
                wait_message_embed.set_footer(text="Please type YES or NO")
                wait_message = await ctx.send(content="{0.author.mention}: Is this the channel you're looking for?".format(ctx), embed=wait_message_embed)
                response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

                if response_message.content.lower() == "no":
                    await ctx.send("{0.author.mention}: Looks like I couldn't find what you're looking for.\nPlease run the command again once you are sure the name is right".format(ctx), delete_after=30.0)
                    raise UserCancelled
                elif response_message.content.lower() != "yes":
                    await ctx.send("{0.author.mention}: I didn't understand your answer.\nPlease run the command and try again.".format(ctx), delete_after=30.0)
                    raise UserCancelled
                else:
                    # User typed yes, continue on
                    pass

                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass

            else:
                try:
                    await wait_message.delete()
                    await response_message.delete()
                except:
                    pass
                raise Exception("Result status was not okay: \n{}".format(result.text))

            try:
                await wait_message.delete()
                await response_message.delete()
            except:
                pass

            # User chose the right channel, now let's ask which channel they want to remove
            wait_message_args = {
                'description': "Which channel(s) should I stop notifying when **{0.name}** goes live?".format(twitch_channel),
                'colour': discord.Colour.dark_purple(),
            }
            wait_message_embed = discord.Embed(**wait_message_args)
            wait_message_embed.add_field(name="Channels", value=", ".join([tn.content_object.name for tn in twitch_notifications]))
            wait_message_embed.set_footer(text="Please mention the channel(s) with the # prefix or type all to remove all of them")
            wait_message = await ctx.send(content="{0.author.mention}".format(ctx), embed=wait_message_embed)
            response_message = await self.bot.wait_for('message', check=author_check, timeout=QUESTION_TIMEOUT)

            if response_message.clean_content.lower() == "all":
                notifications_to_delete = twitch_notifications
            elif len(response_message.channel_mentions) == 0:
                await ctx.send("{0.author.mention}: Looks like you didn't mention any channels to be notified. Please run the command again.".format(ctx), delete_after=30.0)
                raise UserCancelled
            else:
                # User mentioned channels
                notifications_to_delete = twitch_notifications.filter(object_id__in=[c.id for c in response_message.channel_mentions])

            notifications_deleted = []
            for n in notifications_to_delete:
                try:
                    name = n.content_object.name
                    n.delete()
                    notifications_deleted.append(name)
                except:
                    pass

            embed_args = {
                'description': "I will not notify the following channels when **{0.name}** goes live!".format(twitch_channel),
                'colour': discord.Colour.dark_purple(),
            }
            embed = discord.Embed(**embed_args)
            embed.set_thumbnail(url=result['logo'])
            embed.add_field(name="Channels", value=", ".join(notifications_deleted), inline=False)
            app_info = await self.bot.application_info()
            avatar = app_info.owner.default_avatar_url if not app_info.owner.avatar else app_info.owner.avatar_url
            embed.set_footer(text = "Developer/Owner: {0.name}#{0.discriminator} (Shard ID: {1})".format(app_info.owner, ctx.guild.shard_id), icon_url = avatar)
            await ctx.send("{0.author.mention}".format(ctx), embed=embed, delete_after=60.0)

        except asyncio.TimeoutError as te:
            await ctx.send("{} It looks like you took too long to respond. Please run the command again if you wish to continue.".format(ctx.author.mention))
            waiting_for_twitch_name = False
            error_occurred = True

        except UserCancelled as uc:
            # User cancelled option or something wasn't understood
            pass

        except Exception as e:
            Log.objects.create(message="Error running stop command for {0.author.id} {0.author.name}\n{1}\n{2}".format(ctx, logify_exception_info(), e))
            try:
                await ctx.send("{}, Looks like an error ocurred. Please try again.\nIf the issue persists, please alert my owner.".format(ctx.author.mention))
            except:
                pass

        try:
            await ctx.message.delete()
            await wait_message.delete()
            await response_message.delete()
        except:
            pass


def setup(bot):
    bot.add_cog(LiveBot(bot))
