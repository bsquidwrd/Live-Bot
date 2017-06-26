import os
from discord.ext import commands
import discord.utils


def is_owner_check(message):
    """
    Checks if the message author is the Bot owner
    """
    return message.author.id == os.getenv('SQUID_BOT_OWNER_ID', '131224383640436736')

def is_owner():
    """
    Returns True/False depending on if the message author is the Bot Owner
    """
    return commands.check(lambda ctx: is_owner_check(ctx.message))



# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# If these checks fail, then there are two fallbacks.
# A role with the name of Bot Mod and a role with the name of Bot Admin.
# Having these roles provides you access to certain commands without actually having
# the permissions required for them.
# Of course, the owner will always be able to execute commands.

def check_permissions(ctx, perms):
    """
    Checks if the user has a specific permissions
    """
    msg = ctx.message
    if is_owner_check(msg):
        return True

    ch = msg.channel
    author = msg.author
    resolved = ch.permissions_for(author)
    return all(getattr(resolved, name, None) == value for name, value in perms.items())

def role_or_permissions(ctx, check, **perms):
    """
    Checks if the user has permission, either from a Role or just a specific Permission
    """
    if check_permissions(ctx, perms):
        return True

    ch = ctx.message.channel
    author = ctx.message.author
    if ch.is_private:
        return False # can't have roles in PMs

    role = discord.utils.find(check, author.roles)
    return role is not None

def mod_or_permissions(**perms):
    """
    Decorator for `role_or_permissions` or if they have the 'Bot Mod' or 'Bot Admin' role
    """
    def predicate(ctx):
        return role_or_permissions(ctx, lambda r: r.name in ('Bot Mod', 'Bot Admin'), **perms)

    return commands.check(predicate)

def admin_or_permissions(**perms):
    """
    Decorator for `role_or_permissions` or if they have the 'Bot Admin' role
    """
    def predicate(ctx):
        return role_or_permissions(ctx, lambda r: r.name == 'Bot Admin', **perms)

    return commands.check(predicate)

def is_in_servers(*server_ids):
    """
    Decorator for checking if the ctx server is in a list of server_ids
    """
    def predicate(ctx):
        server = ctx.message.server
        if server is None:
            return False
        return server.id in server_ids
    return commands.check(predicate)

def is_personal_server():
    """
    Check if the server is mine or not
    """
    return is_in_servers('225471771355250688', '138036477643718656')
