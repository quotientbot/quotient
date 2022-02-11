from __future__ import annotations

import discord
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog

__all__ = ("SocketScrims",)


class SocketScrims(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


    @Cog.listener()
    async def on__request___scrim_create(self,data):
        ...
    
