from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView
from core import Context

from models.esports.slotm import ScrimsSlotManager

import discord


__all__ = ("ScrimsSlotManagerSetup",)


class ScrimSlotManagerSetup(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=60, title="Scrims Slot Manager")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    async def initial_message(guild: discord.Guild):
        _e = discord.Embed()

        return _e

    @discord.ui.button(label="Add Channel", custom_id="scrims_slotm_addc")
    async def add_channel(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Edit Config", custom_id="scrims_slotm_addc")
    async def edit_config(self, button: discord.Button, interaction: discord.Interaction):
        ...
