from __future__ import annotations

import asyncio
import re
import typing as T
from contextlib import suppress

import discord

from models import ArrayRemove, AssignedSlot, Scrim, ScrimsSlotManager
from utils import BaseSelector, emote

from ..public import ScrimsSlotmPublicView

claim_lock = asyncio.Lock()

__all__ = ("ScrimsClaim",)
#!TODO: do some processing on the team name


class ScrimsClaim(discord.ui.Button):
    view: ScrimsSlotmPublicView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        if not self.view.claimable:  # this can never be true but still
            await interaction.response.send_message("No slot available right now.", ephemeral=True)
            return await self.view.record.refresh_public_message()

        await interaction.response.defer(thinking=True, ephemeral=True)
        claim_view = BaseSelector(
            interaction.user.id,
            ClaimSlotSelector,
            scrims=self.view.claimable,
            multiple_slots=self.view.record.multiple_slots,
        )
        await interaction.followup.send("Select the slot you want to claim:", view=claim_view, ephemeral=True)


class ClaimSlotModal(discord.ui.Modal, title="Claim Scrims Slot"):
    multiple_slots: bool
    selected_slot: str

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        team_name = str(self.children[0])
        scrim_id, num = self.selected_slot.split(":")
        num = int(num)

        team_name = "Team " + re.sub(r"team|name|[^\w\s]", "", team_name.lower()).strip().title()

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if not scrim:
            return await interaction.followup.send("Scrim not found.", ephemeral=True)

        if await scrim.banned_teams.filter(user_id=interaction.user.id).exists():
            return await interaction.followup.send("You are banned from this scrim.", ephemeral=True)

        if not self.multiple_slots:
            if await scrim.assigned_slots.filter(user_id=interaction.user.id).exists():
                return await interaction.followup.send("You already have a slot in this scrim.", ephemeral=True)

        async with claim_lock:
            await scrim.refresh_from_db(("available_slots",))

            if num not in scrim.available_slots:
                return await interaction.followup.send("Somebody claimed this slot before you.", ephemeral=True)

            await Scrim.filter(pk=scrim_id).update(available_slots=ArrayRemove("available_slots", num))

            scrim.bot.loop.create_task(self.add_role(interaction.user, scrim.role_id))

            user_id = interaction.user.id
            _slot = await AssignedSlot.create(num=num, user_id=user_id, members=[user_id], team_name=team_name)
            await scrim.assigned_slots.add(_slot)

            scrim.bot.loop.create_task(self.proccess_claim(scrim, _slot))
            await interaction.followup.send(f"{emote.check} Slot claimed successfully.", ephemeral=True)

    async def add_role(self, user: discord.Member, role_id: int):
        with suppress(discord.HTTPException):
            if not user._roles.has(role_id):
                await user.add_roles(discord.Object(id=role_id))

    async def proccess_claim(self, scrim: Scrim, slot: AssignedSlot):
        await scrim.refresh_slotlist_message()

        await ScrimsSlotManager.refresh_guild_message(scrim.guild_id, scrim.id)

        with suppress(AttributeError, discord.HTTPException):
            await scrim.slotlist_channel.send(f"{slot.team_name} ({slot.owner.mention}) -> Claimed Slot {slot.num}")


class ClaimSlotSelector(discord.ui.Select):
    view: BaseSelector

    def __init__(self, scrims: T.List[Scrim], multiple_slots: bool):

        _options = []
        for scrim in scrims:
            slots = sorted(scrim.available_slots)

            _options.append(
                discord.SelectOption(
                    label=f"Slot {slots[0]} ─ #{getattr(scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{scrim.name} (ID: {scrim.id})",
                    value=f"{scrim.id}:{slots[0]}",
                    emoji="📇",
                )
            )

        super().__init__(options=_options)
        self.multiple_slots = multiple_slots

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()

        v = ClaimSlotModal()
        v.multiple_slots = self.multiple_slots
        v.selected_slot = interaction.data["values"][0]

        v.add_item(
            discord.ui.TextInput(
                label="Team Name",
                style=discord.TextStyle.short,
                placeholder="Enter your team name here...",
                min_length=3,
                max_length=25,
            )
        )
        await interaction.response.send_modal(v)
