from discord.ext import commands
from discord.ext.commands import Context, has_any_role, CheckFailure
from typing import Union


# TODO: shift these to exceptions.py
class SMNotUsable(commands.CheckFailure):
    pass


class PastTime(commands.CheckFailure):
    pass


class InvalidTime(commands.CheckFailure):
    pass


def can_use_sm():
    """
    Returns True if the user has manage roles or scrim-mod role in the server.
    """

    async def predicate(ctx):
        if ctx.author.guild_permissions.manage_guild or "scrims-mod" in [role.name.lower() for role in ctx.author.roles]:
            return True
        else:
            raise SMNotUsable()

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
