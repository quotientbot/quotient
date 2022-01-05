from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView

from core import Context
from models.esports.slotm import ScrimsSlotManager

import discord


class ScrimsSlotmEditor(EsportsBaseView):
    def __init__(self, ctx: Context, *, record: ScrimsSlotManager):
        super().__init__(ctx, timeout=60, title="Slot-M Editor")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot
        self.record = record

    @classmethod
    async def initial_embed(cls):
        _e = discord.Embed()
        return _e
