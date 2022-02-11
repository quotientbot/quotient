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
    async def on__request___scrim_create(self, data: BaseScrim):
        _v = await data.validate_perms(self.bot)

        if not all(_v):
            return await self.bot.sio.emit("scrim_create", SockResponse(ok=False, error=_v[1]))

        await data.create_scrim()
        await self.bot.sio.emit("scrim_create", SockResponse().to_dict())

    @Cog.listener()
    async def on__request___scrim_edit(self, data: BaseScrim):
        _v = await data.validate_perms(self.bot)

        if not all(_v):
            return await self.bot.sio.emit("scrim_edit", SockResponse(ok=False, error=_v[1]))

        await data.edit_scrim()
        await self.bot.sio.emit("scrim_edit", SockResponse().to_dict())
