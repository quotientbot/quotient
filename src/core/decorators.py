from __future__ import annotations


from functools import wraps
from .Cog import Cog

import discord
from .cache import CacheManager


class right_bot_check:
    def __call__(self, fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):

            if isinstance(args[0], Cog):
                bot = args[0].bot

            else:
                bot = args[0]

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
