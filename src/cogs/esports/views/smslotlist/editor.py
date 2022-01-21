from __future__ import annotations


from core import Context
import discord

from models import Scrim
from models.esports.scrims import AssignedSlot

from .select import prompt_slot_selection


__all__ = ("ScrimsSlotlistEditor",)


class ScrimsSlotlistEditor(discord.ui.View):
    message: discord.Message

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(timeout=30)

        self.ctx = ctx
        self.scrim = scrim

    async def on_timeout(self) -> None:
        if not hasattr(self, "message"):
            return

        for _ in self.children:
            if isinstance(_, discord.ui.Button):
                _.disabled = True

        return await self.message.edit(embed=self.message.embeds[0], view=self)

    def initial_embed(self) -> discord.Embed:
        _e = discord.Embed(color=0x00FFB3, description="Choose an option below to edit the slotlist.")
        return _e

    @discord.ui.button(style=discord.ButtonStyle.success, label="Change Team", custom_id="smslot_change_team")
    async def change_team_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        _v = await prompt_slot_selection(
            await self.scrim.assigned_slots.all().order_by("num"), placeholder="Select the slot to change..."
        )
        await interaction.followup.send("Kindly choose a slot from the dropdown.", view=_v, ephemeral=True)

        await _v.wait()
        if _v.custom_id:
            _slot = await AssignedSlot.get(pk=_v.custom_id)

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Team", custom_id="smslot_remove_team")
    async def remove_team_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        _v = await prompt_slot_selection(
            await self.scrim.assigned_slots.all().order_by("num"), placeholder="Select the slot to remove..."
        )
        await interaction.followup.send("Kindly choose a slot from the dropdown.", view=_v, ephemeral=True)

        await _v.wait()
        if _v.custom_id:
            ...
