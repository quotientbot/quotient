from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView
from core import Context

from models.esports.slotm import ScrimsSlotManager

import discord

from utils import channel_input


__all__ = ("ScrimsSlotManagerSetup",)


class ScrimSlotManagerSetup(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=60, title="Scrims Slot Manager")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    async def initial_message(guild: discord.Guild):
        records = await ScrimsSlotManager.filter(guild_id=guild.id)
        _to_show = [_.__str__() for _ in records]

        _sm = "\n".join(_to_show) if _to_show else "```No scrims slot managers found.```"

        _e = discord.Embed(color=0x00FFB3, title=f"Scrims Slot-Manager Setup")

        _e.description = f"Current slot-manager channels:\n{_sm}"
        return _e

    @discord.ui.button(label="Add Channel", custom_id="scrims_slotm_addc")
    async def add_channel(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Edit Config", custom_id="scrims_slotm_addc")
    async def edit_config(self, button: discord.Button, interaction: discord.Interaction):
        ...

