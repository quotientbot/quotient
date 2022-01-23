from __future__ import annotations
from contextlib import suppress


from core import Context
import discord

from models import Scrim
from models.esports.scrims import AssignedSlot

from .select import prompt_slot_selection

import asyncio
import re
from utils import truncate_string

__all__ = ("ScrimsSlotlistEditor",)


class ScrimsSlotlistEditor(discord.ui.View):
    message: discord.Message

    def __init__(self, ctx: Context, scrim: Scrim, slotlist_message: discord.Message):
        super().__init__(timeout=30)

        self.ctx = ctx
        self.scrim = scrim
        self.slotlist_message = slotlist_message

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

        _e = discord.Embed(color=0x00FFB3, description="Kindly choose a slot from the dropdown.")

        await interaction.followup.send(embed=_e, view=_v, ephemeral=True)

        await _v.wait()
        if slot_id := _v.custom_id:
            _slot = await AssignedSlot.get_or_none(pk=slot_id)

            _e.description = "Please enter the team name. Also mention the leader of that team (Optional)"
            await interaction.followup.send(embed=_e, ephemeral=True)

            try:
                _ms: discord.Message = await self.ctx.bot.wait_for(
                    "message",
                    check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                    timeout=50,
                )
            except asyncio.TimeoutError:
                return await interaction.followup.send("Timed out. Please try again.", ephemeral=True)

            await _ms.delete()
            user_id = None
            if _ms.mentions:
                user_id = _ms.mentions[0].id

                with suppress(discord.HTTPException):
                    await _ms.mentions[0].add_roles(discord.Object(id=self.scrim.role_id))

            _ms.content = re.sub(r"<@*!*&*\d+>", "", _ms.content)

            team_name = truncate_string(_ms.content, 22)
            if not team_name:
                return await interaction.followup.send("Team name cannot be empty.", ephemeral=True)

            await AssignedSlot.filter(pk=slot_id).update(team_name=team_name, user_id=user_id)

            if _slot:
                if not await self.scrim.assigned_slots.filter(user_id=_slot.user_id).exists():
                    member = self.ctx.guild.get_member(_slot.user_id)
                    with suppress(discord.HTTPException):
                        await member.remove_roles(discord.Object(id=self.scrim.role_id))

            _e.description = "Slotlist updated successfully."
            await interaction.followup.send(embed=_e, ephemeral=True)
            return await self.scrim.refresh_slotlist_message(self.slotlist_message)

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
