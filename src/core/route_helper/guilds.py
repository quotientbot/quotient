from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient


from models import Guild


async def update_guild_cache(bot: Quotient, guild_id: int) -> dict:
    guild = await Guild.get(guild_id=int(guild_id))

    self.bot.cache.guild_data[guild.guild_id] = {
        "prefix": guild.prefix,
        "color": guild.embed_color,
        "footer": guild.embed_footer,
    }

    return {"ok": True, "result": {}, "error": None}
