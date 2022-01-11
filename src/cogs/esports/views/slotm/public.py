from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from models.esports.slotm import ScrimsSlotManager
from contextlib import suppress
import discord

__all__ = ("ScrimsSlotmPublicView",)


class ScrimsSlotmPublicView(discord.ui.View):
    def __init__(self, bot: Quotient, *, record: ScrimsSlotManager):
        super().__init__(timeout=None)

        self.bot = bot

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="scrims_slot_cancel", label="Cancel Slot")
    async def cancel_scrims_slot(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="scrims_slot_claim", label="Claim Slot")
    async def claim_scrims_slot(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Remind Me", custom_id="scrims_slot_reminder", emoji="🔔")
    async def set_slot_reminder(self, button: discord.Button, interaction: discord.Interaction):
        ...
