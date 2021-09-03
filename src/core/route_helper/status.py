from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient


async def get_status(bot: Quotient) -> dict:
    _list = []
    for id, shard in bot.shards.items():
        _list.append(
            {
                "id": id,
                "latency": shard.latency,
                "status": not shard.is_closed(),
                "guilds": sum(1 for guild in bot.guilds if guild.shard_id == id),
                "unavailable": sum(1 for guild in bot.guilds if guild.unavailable),
            }
        )

    return _list
