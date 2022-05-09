from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog
from models import Scrim

from ..schemas import BaseScrim, SockResponse

__all__ = ("SocketScrims",)


class SocketScrims(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_request__bot_scrim_create(self, u: str, data: dict):
        data: BaseScrim = BaseScrim(**data)

        _v = await data.validate_perms(self.bot)

        if all(_v):
            _v = await data.create_scrim(self.bot)

        if not all(_v):
            return await self.bot.sio.emit("bot_scrim_create__{0}".format(u), SockResponse(ok=False, error=_v[1]).dict())

        await self.bot.sio.emit("bot_scrim_create__{0}".format(u), SockResponse(data={"id": _v[1].id}).dict())

    @Cog.listener()
    async def on_request__bot_scrim_edit(self, u: str, data: dict):
        data: BaseScrim = BaseScrim(**data)

        _v = await data.validate_perms(self.bot)

        if not all(_v):
            return await self.bot.sio.emit("bot_scrim_edit__{0}".format(u), SockResponse(ok=False, error=_v[1]).dict())

        await data.update_scrim(self.bot)
        await self.bot.sio.emit(f"bot_scrim_edit__{u}", SockResponse().dict())

    @Cog.listener()
    async def on_request__bot_scrim_delete(self, u: str, data: dict):
        guild_id, scrim_id = data["guild_id"], data["scrim_id"]
        if scrim_id:
            scrim = await Scrim.get_or_none(pk=scrim_id)
            if scrim:
                await scrim.full_delete()

        else:
            scrims = await Scrim.filter(guild_id=guild_id)
            for scrim in scrims:
                await scrim.full_delete()

        return await self.bot.sio.emit(f"bot_scrim_delete__{u}", SockResponse().dict())
