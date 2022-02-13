from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Cog
from ..schemas import SockResponse


class SockSettings(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_request__prefix_change(self, u, data: dict):
        guild_id = data.get("guild_id")
        await self.bot.cache.update_guild_cache(int(guild_id))
        await self.bot.sio.emit("prefix_change__{0}".format(u), SockResponse().dict())
