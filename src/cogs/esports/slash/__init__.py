from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from core import Cog

from .scrims import *

__all__ = ("SlashCog",)


class SlashCog(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def cog_load(self) -> None:
        await self.bot.add_cog(ScrimsSlash(self.bot))
