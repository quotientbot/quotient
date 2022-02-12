from __future__ import annotations

import discord
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from ..schemas import BaseScrim, SockResponse
from core import Cog

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
