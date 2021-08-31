from contextlib import suppress
from cogs.esports.helpers.views import update_channel_for
from models.esports import SlotManager
from models.esports.slots import SlotLocks
from models.helpers import ArrayAppend, ArrayRemove
from utils import emote, BaseSelector, Prompt
from datetime import datetime
from constants import IST
from typing import List, NamedTuple
from models import Scrim, AssignedSlot
import discord
import asyncio

from collections import Counter

from utils.formats import truncate_string

from ..helpers import get_slot_manager_message, free_slots, send_sm_logs, SlotLogType

__all__ = ("ScrimSelector", "SlotManagerView")


class ScrimSlot(NamedTuple):
    slots: List[int]
    scrim: Scrim


class CancelSlot(NamedTuple):
    obj: AssignedSlot
    scrim: Scrim


class ScrimSelector(discord.ui.Select):
    def __init__(self, placeholder: str, scrims: List[Scrim]):

        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=scrim.name,
                    value=scrim.id,
                    description=f"{scrim.registration_channel} (ScrimID: {scrim.id})",
                    emoji=emote.category,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class ClaimSlotSelector(discord.ui.Select):
    def __init__(self, placeholder: str, slots: List[ScrimSlot]):

        _options = []
        for slot in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.slots[0]} ─ {getattr(slot.scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{slot.scrim.name} (ID: {slot.scrim.id})",
                    value=f"{slot.scrim.id}:{slot.slots[0]}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class CancelSlotSelector(discord.ui.Select):
    def __init__(self, placeholder: str, slots: List[CancelSlot]):

        _options = []
        for slot in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.obj.num} ─ {getattr(slot.scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{slot.obj.team_name} (ID: {slot.scrim.id})",
                    value=f"{slot.scrim.id}:{slot.obj.id}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class SlotManagerView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="cancel-slot", label="Cancel Your Slot")
    async def cancel_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        main_record = await SlotManager.get_or_none(message_id=interaction.message.id, guild_id=interaction.guild_id)

        if not main_record:
            return await interaction.followup.send("Slot-Manager setup was deleted. You need to setup again.")

        _slots = []
        async for scrim in Scrim.filter(guild_id=interaction.guild_id):
            if lock := await SlotLocks.get_or_none(pk=scrim.id):
                if lock and lock.locked:
                    continue

            async for slot in scrim.assigned_slots.filter(user_id=interaction.user.id):
                _slots.append(CancelSlot(slot, scrim))

        if not _slots:
            return await interaction.followup.send(
                "You haven't registred in any scrim today.\nOr maybe the slotmanager is locked for that scrim.",
                ephemeral=True,
            )

        cancel_view = BaseSelector(interaction.user.id, CancelSlotSelector, placeholder="select a slot", slots=_slots)
        await interaction.followup.send("Choose a slot to cancel", view=cancel_view, ephemeral=True)
        await cancel_view.wait()

        if c_id := cancel_view.custom_id:
            prompt = Prompt(interaction.user.id)
            await interaction.followup.send("Are you sure you want to cancel your slot?", view=prompt, ephemeral=True)
            await prompt.wait()
            if not prompt.value:
                return await interaction.followup.send("Alright, Aborting.", ephemeral=True)

            scrim_id, slot_id = c_id.split(":")
            scrim = await Scrim.get(pk=scrim_id)

            with suppress(AttributeError, discord.Forbidden, discord.HTTPException):
                await interaction.user.remove_roles(discord.Object(id=scrim.role_id))

            await AssignedSlot.filter(pk=slot_id).update(team_name="Cancelled Slot")

            slot = await AssignedSlot.get(pk=slot_id)
            embed, channel = await scrim.create_slotlist()

            msg = await channel.fetch_message(scrim.slotlist_message_id)
            if msg:
                await msg.edit(embed=embed)

            else:
                await channel.send(embed=embed)

            await AssignedSlot.filter(pk=slot_id).delete()

            await Scrim.filter(pk=scrim_id).update(available_slots=ArrayAppend("available_slots", slot.num))

            _free = await free_slots(interaction.guild_id)
            self.children[1].disabled = False
            if not _free:
                self.children[1].disabled = True

            sm = await SlotManager.get(guild_id=interaction.guild_id)
            msg = await sm.message
            await msg.edit(embed=await get_slot_manager_message(interaction.guild_id, _free), view=self)

            await interaction.followup.send("Alright, Cancelled your slot.", ephemeral=True)

            reg_channel = getattr(scrim.registration_channel, "mention", "channel-deleted")
            await send_sm_logs(main_record, SlotLogType.public, f"Slot {slot.num} ({reg_channel}) is free to be claimed.")

            await send_sm_logs(
                main_record,
                SlotLogType.private,
                f"{interaction.user.mention} cancelled their Slot {slot.num} ({reg_channel})",
            )

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="claim-slot", label="Claim Slot")
    async def claim_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        main_record = await SlotManager.get_or_none(message_id=interaction.message.id, guild_id=interaction.guild_id)

        if not main_record:
            return await interaction.followup.send("Slot-Manager setup was deleted. You need to setup again.")

        perms = interaction.channel.permissions_for(interaction.guild.me)
        if not perms.manage_channels and perms.manage_messages:
            return await interaction.followup.send(
                "I need `manage_channels` & `manage_messages` permissions in this channel to work properly."
            )

        _time = datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)
        records = Scrim.filter(guild_id=interaction.guild_id, closed_at__gte=_time, available_slots__not=[])

        _slots = []
        async for record in records:
            if lock := await SlotLocks.get_or_none(pk=record.id):
                if lock and lock.locked:
                    continue

            _slots.append(ScrimSlot(sorted(record.available_slots), record))

        if not _slots:
            return await interaction.followup.send(
                "There is no slot available right now. Please try again later.", ephemeral=True
            )

        if len(_slots) > 25:
            return await interaction.followup.send(
                "More than 25 slots are available. Please contact moderators.", ephemeral=True
            )

        claim_view = BaseSelector(interaction.user.id, ClaimSlotSelector, placeholder="select slot", slots=_slots)
        await interaction.followup.send("Choose a slot to claim", view=claim_view, ephemeral=True)
        await claim_view.wait()
        if c_id := claim_view.custom_id:
            scrim_id, num = c_id.split(":")
            scrim = await Scrim.get_or_none(pk=scrim_id)

            if not scrim:
                return await interaction.followup.send("Scrim not found.", ephemeral=True)

            await update_channel_for(interaction.channel, interaction.user)

            await interaction.followup.send("What is your team's name?", ephemeral=True)
            try:
                team_name = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id,
                    timeout=30,
                )
            except asyncio.TimeoutError:
                await update_channel_for(interaction.channel, interaction.user, False)
                return await interaction.followup.send("Timed out. Please try again.", ephemeral=True)

            await team_name.delete()
            await update_channel_for(interaction.channel, interaction.user, False)

            await Scrim.filter(pk=scrim_id).update(available_slots=ArrayRemove("available_slots", num))
            with suppress(discord.Forbidden, discord.HTTPException, AttributeError):
                await interaction.user.add_roles(discord.Object(id=scrim.role_id))

            slot = await AssignedSlot.create(
                num=num, user_id=interaction.user.id, team_name=truncate_string(team_name.content, 22)
            )
            await scrim.assigned_slots.add(slot)

            embed, channel = await scrim.create_slotlist()

            msg = await channel.fetch_message(scrim.slotlist_message_id)
            if msg:
                await msg.edit(embed=embed)

            else:
                await channel.send(embed=embed)

            _free = await free_slots(interaction.guild_id)
            self.children[1].disabled = False
            if not _free:
                self.children[1].disabled = True

            sm = await SlotManager.get(guild_id=interaction.guild_id)
            msg = await sm.message
            await msg.edit(embed=await get_slot_manager_message(interaction.guild_id, _free), view=self)
            await interaction.followup.send("Slot claimed successfully.", ephemeral=True)

            reg_channel = getattr(scrim.registration_channel, "mention", "channel-deleted")

            await send_sm_logs(
                main_record, SlotLogType.private, f"{interaction.user.mention} claimed Slot {num} ({reg_channel})"
            )
