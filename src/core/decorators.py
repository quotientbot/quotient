from __future__ import annotations

from contextlib import suppress
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

import discord

from core.Context import Context

from .cache import CacheManager
from .Cog import Cog

__all__ = ("right_bot_check", "event_bot_check", "role_command_check")


class right_bot_check:
    def __call__(self, fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            if TYPE_CHECKING:
                from .Bot import Quotient

            if isinstance(args[0], Cog):
                bot: Quotient = args[0].bot

            else:
                bot: Quotient = args[0]  # type: ignore

            with suppress(AttributeError):
                for arg in args:
                    # check for both guild and guild_id
                    if hasattr(arg, "guild"):
                        guild_id = arg.guild.id
                        break
                    elif hasattr(arg, "guild_id"):
                        guild_id = arg.guild_id
                        break
                else:
                    _obj = kwargs.get("guild") or kwargs.get("guild_id")
                    # guild id can be none here
                    guild_id = _obj.id if isinstance(_obj, discord.Guild) else _obj

                if guild_id is not None and not await CacheManager.match_bot_guild(guild_id, bot.user.id):
                    return

            return await fn(*args, **kwargs)

        return wrapper


class event_bot_check:
    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    def __call__(self, fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            bot_id: int = args[0].bot.user.id
            return await fn(*args, **kwargs) if bot_id == self.bot_id else None

        return wrapper


class role_command_check:
    def __call__(self, fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any):
            _, ctx, *role = args

            role: discord.Role = role[0] if isinstance(role, list) else role  # type: ignore
            ctx: Context  # type: ignore

            if role.managed:
                return await ctx.error(f"Role is an integrated role and cannot be added manually.")

            if ctx.me.top_role.position <= role.position:
                return await ctx.error(f"The position of {role.mention} is above my toprole ({ctx.me.top_role.mention})")

            if not ctx.author == ctx.guild.owner and ctx.author.top_role.position <= role.position:
                return await ctx.error(
                    f"The position of {role.mention} is above your top role ({ctx.author.top_role.mention})"
                )

            if role.permissions > ctx.author.guild_permissions:
                return await ctx.error(f"{role.mention} has higher permissions than you.")

            if role.permissions.administrator:
                return await ctx.error(f"{role.mention} has administrator permissions.")

            return await fn(*args, **kwargs)

        return wrapper
