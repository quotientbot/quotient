from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Cog
from models import Tourney

from ..schemas import SockTourney

__all__ = ("SockTourney",)


class SockTourney(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_request__bot_tourney_create(self, u: str, data: dict):
        data: SockTourney = SockTourney(**data)

    @Cog.listener()
    async def on_request__bot_tourney_edit(self, u: str, data: dict):
        data: SockTourney = SockTourney(**data)

    @Cog.listener()
    async def on_request__bot_tourney_delete(self, u: str, data: dict):
        guild_id, tourney_id = data["guild_id"], data["tourney_id"]
        if tourney_id:
            tourney = await Tourney.get_or_none(pk=tourney_id)
            if tourney:
                await tourney.full_delete()

        else:
            tourneys = await Tourney.filter(guild_id=guild_id)
            for tourney in tourneys:
                await tourney.full_delete()

        return await self.bot.sio.emit("bot_tourney_delete__{0}".format(u), SockTourney().dict())
