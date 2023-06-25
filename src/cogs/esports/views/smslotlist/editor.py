from __future__ import annotations

import asyncio
import re
import typing as T
from contextlib import suppress

import discord

from models import (ArrayAppend, ArrayRemove, AssignedSlot, Scrim,
                    ScrimsSlotManager)
from utils import emote, truncate_string

from .select import prompt_slot_selection

if T.TYPE_CHECKING:
    from core import Quotient

__all__ = ("ScrimsSlotlistEditor",)


class ScrimsSlotlistEditor(discord.ui.View):
    message: discord.Message

    def __init__(self, bot: Quotient, scrim: Scrim, slotlist_message: discord.Message):
        super().__init__(timeout=30)

        self.bot = bot
        self.scrim = scrim
        self.slotlist_message = slotlist_message

        self.custom_id = None

    async def on_timeout(self) -> None:
        if not hasattr(self, "message"):
            return

        for _ in self.children:
            if isinstance(_, discord.ui.Button):
                _.disabled = True

        with suppress(discord.HTTPException):
            return await self.message.edit(view=self)

    def initial_embed(self) -> discord.Embed:
        _e = discord.Embed(color=0x00FFB3, description="Choose an option below to edit the slotlist.")
        return _e

    @discord.ui.button(style=discord.ButtonStyle.success, label="Change Team", custom_id="smslot_change_team")
    async def change_team_name(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

        __slots = await self.scrim.assigned_slots.all().order_by("num")
        if not __slots:
            return await interaction.followup.send("No slot available to replace.", ephemeral=True)
        _v = await prompt_slot_selection(__slots, placeholder="Select the slot to change...")

        _e = discord.Embed(color=0x00FFB3, description="Kindly choose a slot from the dropdown.")

        await interaction.followup.send(embed=_e, view=_v, ephemeral=True)

        await _v.wait()
        if slot_id := _v.custom_id:
            _slot = await AssignedSlot.get_or_none(pk=slot_id)

            _e.description = "Please enter the team name. Also mention the leader of that team (Optional)"
            await interaction.followup.send(embed=_e, ephemeral=True)

            try:
                _ms: discord.Message = await self.bot.wait_for(
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

            if _slot and _slot.user_id:
                if not await self.scrim.assigned_slots.filter(user_id=_slot.user_id).exists():
                    member = self.scrim.guild.get_member(_slot.user_id)
                    with suppress(discord.HTTPException):
                        await member.remove_roles(discord.Object(id=self.scrim.role_id))

            _e.description = "Slotlist updated successfully."
            await interaction.followup.send(embed=_e, ephemeral=True)
            return await self.scrim.refresh_slotlist_message(self.slotlist_message)

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Team", custom_id="smslot_remove_team")
    async def remove_team_name(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

        __slots = await self.scrim.assigned_slots.all().order_by("num")
        if not __slots:
            return await interaction.followup.send("No slot available to remove.", ephemeral=True)

        _v = await prompt_slot_selection(__slots, placeholder="Select the slot to remove...")
        await interaction.followup.send("Kindly choose a slot from the dropdown.", view=_v, ephemeral=True)

        await _v.wait()
        if slot_id := _v.custom_id:

            _slot = await AssignedSlot.get_or_none(pk=slot_id)
            if not _slot:
                return

            if _slot.user_id:
                if await self.scrim.assigned_slots.filter(user_id=_slot.user_id).count() == 1:
                    with suppress(discord.HTTPException, AttributeError):
                        m = self.scrim.guild.get_member(_slot.user_id)
                        await m.remove_roles(discord.Object(id=self.scrim.role_id))

            await self.scrim.make_changes(available_slots=ArrayAppend("available_slots", _slot.num))
            await AssignedSlot.filter(pk=slot_id).update(team_name="❌")
            await self.scrim.refresh_slotlist_message(self.slotlist_message)

            await AssignedSlot.filter(pk=slot_id).delete()

            _e = discord.Embed(color=0x00FFB3, description="Team Removed from slotlist.")

            await interaction.followup.send(embed=_e, ephemeral=True)

            slotm = await ScrimsSlotManager.get_or_none(guild_id=self.scrim.guild_id, scrim_ids__contains=self.scrim.id)
            if slotm:
                await slotm.refresh_public_message()

    @discord.ui.button(label="Add Team", custom_id="smslot_add_team", style=discord.ButtonStyle.green)
    async def add_new_team(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

        _list = list(range(self.scrim.start_from, 30))
        async for _ in self.scrim.assigned_slots.order_by("num"):
            _list.remove(_.num)

        _slots = [AssignedSlot(num=_, id=_, team_name="Click to add") for _ in _list]
        if not _slots:
            return await interaction.followup.send("No slots available to add this time.", ephemeral=True)

        _v = await prompt_slot_selection(_slots, placeholder="Select the slot to add...")

        await interaction.followup.send("Kindly choose a slot from the dropdown.", view=_v, ephemeral=True)
        await _v.wait()
        if slot_id := _v.custom_id:
            await interaction.followup.send(
                "Please enter the team name. Also mention the leader of that team (Optional)", ephemeral=True
            )

            try:
                _ms: discord.Message = await self.bot.wait_for(
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

            _slot = await AssignedSlot.create(num=slot_id, team_name=team_name, user_id=user_id)
            await self.scrim.assigned_slots.add(_slot)
            await self.scrim.make_changes(available_slots=ArrayRemove("available_slots", slot_id))

            await self.scrim.refresh_slotlist_message(self.slotlist_message)

            return await interaction.followup.send(f"{emote.check} Team added successfully.", ephemeral=True)
