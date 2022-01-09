from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from models.esports.slotm import ScrimsSlotManager
from contextlib import suppress
import discord

__all__ = ("ScrimsSlotmPublicView",)


class ScrimSlotmPublicView(discord.ui.View):
    def __init__(self, bot: Quotient, *, record: ScrimsSlotManager):
        super().__init__(timeout=None)

        self.bot = bot

    @staticmethod
    async def initial_embed(record: ScrimsSlotManager):
        _e = discord.Embed(color=0x00FFB3)
        return _e

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="scrims_slot_cancel", label="Cancel Slot")
    async def cancel_scrims_slot(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="scrims_slot_claim", label="Claim Slot")
    async def claim_scrims_slot(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Set Reminder", custom_id="scrims_slot_reminder")
    async def set_slot_reminder(self, button: discord.Button, interaction: discord.Interaction):
        ...
