from __future__ import annotations

from ...views.base import EsportsBaseView

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core import Quotient

from models import Tourney
from core import Context
import discord


class TourneySlotlistManager(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney, size: int):
        super().__init__(ctx, timeout=60, title="Tourney Slotlist Manager")

        self.tourney = tourney
        self.ctx = ctx
        self.size = size
        self.bot: Quotient = ctx.bot

    @staticmethod
    def initial_message(tourney: Tourney) -> discord.Embed:
        _e = discord.Embed()

        return _e
