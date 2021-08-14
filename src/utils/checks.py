from discord.ext import commands
from discord.ext.commands import Context, has_any_role, CheckFailure
from typing import Union
from .exceptions import *
from models import User, Guild


def has_done_setup():
    async def predicate(ctx: Context):
        check = await Guild.get_or_none(pk=ctx.guild.id)
        if not check.private_ch:
            raise NotSetup()

        else:
            return True

    return commands.check(predicate)


def is_premium_guild():
    async def predictate(ctx: Context):
        check = await Guild.get_or_none(guild_id=ctx.guild.id)
        if not check or check.is_premium is False:
            raise NotPremiumGuild()

        else:
            return True

    return commands.check(predictate)


def is_premium_user():
    async def predicate(ctx: Context):
        check = await User.get_or_none(user_id=ctx.author.id)
        if not check or check.is_premium is False:
            raise NotPremiumUser()

        else:
            return True

    return commands.check(predicate)


def can_use_sm():
    """
    Returns True if the user has manage roles or scrim-mod role in the server.
    """

    async def predicate(ctx: Context):
        if ctx.author.guild_permissions.manage_guild or "scrims-mod" in (role.name.lower() for role in ctx.author.roles):
            return True
        raise SMNotUsable()

    return commands.check(predicate)


def can_use_tm():
    """
    Returns True if the user has manage roles or scrim-mod role in the server.
    """

    async def predicate(ctx: Context):
        if ctx.author.guild_permissions.manage_guild or "tourney-mod" in (role.name.lower() for role in ctx.author.roles):
            return True
        raise TMNotUsable()

    return commands.check(predicate)


async def has_any_role_check(ctx: Context, *roles: Union[str, int]) -> bool:
    """
    Returns True if the context's author has any of the specified roles.
    `roles` are the names or IDs of the roles for which to check.
    False is always returns if the context is outside a guild.
    """
    try:
        return await has_any_role(*roles).predicate(ctx)
    except CheckFailure:
        return False


async def check_guild_permissions(ctx: Context, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def is_mod():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {"manage_guild": True})

    return commands.check(pred)


def is_admin():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {"administrator": True})

    return commands.check(pred)


async def check_permissions(ctx: Context, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check)

    return commands.check(pred)
