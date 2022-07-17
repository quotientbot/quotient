from __future__ import annotations

import typing as T
from contextlib import suppress

import discord
from models import ArrayAppend, AssignedSlot, Scrim
from utils import BaseSelector, Prompt, plural, emote

from ..public import ScrimsSlotmPublicView

__all__ = ("ScrimsCancel",)


class ScrimsCancel(discord.ui.Button):
    view: ScrimsSlotmPublicView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not (slots := await self.view.record.user_slots(interaction.user.id)):
            return await interaction.followup.send("You have no slots that can be cancelled.", ephemeral=True)

        cancel_view = BaseSelector(interaction.user.id, CancelSlotSelector, bot=self.view.bot, records=slots)
        await interaction.followup.send("Select the slots you want to remove:", view=cancel_view, ephemeral=True)
        await cancel_view.wait()
        if not cancel_view.custom_id:
            return

        p_str = f"{plural(cancel_view.custom_id):slot|slots}"
        prompt = Prompt(interaction.user.id)
        await interaction.followup.send(
            f"Your `{p_str}` will be cancelled.\n" "*`Are you sure you want to continue?`*",
            view=prompt,
            ephemeral=True,
        )
        await prompt.wait()
        if not prompt.value:
            return await interaction.followup.send("Alright, Aborting.", ephemeral=True)

        m = await interaction.followup.send(f"Cancelling your `{p_str}`... {emote.loading}", ephemeral=True)
        for _ in cancel_view.custom_id:
            scrim_id, slot_id = _.split(":")

            scrim = await Scrim.get_or_none(pk=scrim_id)
            if not scrim:
                continue

            if not await scrim.assigned_slots.filter(user_id=interaction.user.id, pk__not=slot_id).exists():
                with suppress(discord.HTTPException):
                    if interaction.user._roles.has(scrim.role_id):
                        await interaction.user.remove_roles(discord.Object(id=scrim.role_id))

            _slot = await AssignedSlot.filter(pk=slot_id).first()

            await AssignedSlot.filter(pk=slot_id).update(team_name="Cancelled Slot")
            await scrim.refresh_slotlist_message()
            await _slot.delete()

            await Scrim.filter(pk=scrim_id).update(available_slots=ArrayAppend("available_slots", _slot.num))

            link = f"https://discord.com/channels/{scrim.guild_id}/{interaction.channel_id}/{self.view.record.message_id}"
            await scrim.dispatch_reminders(_slot, interaction.channel, link)

        await m.edit(content=f"Alright, Cancelled your `{p_str}`.")
        await self.view.record.refresh_public_message()


class CancelSlotSelector(discord.ui.Select):
    view: BaseSelector

    def __init__(self, bot, records):
        _options = []
        for record in records[:25]:
            reg_channel = bot.get_channel(record["registration_channel_id"])
            _options.append(
                discord.SelectOption(
                    label=f"Slot {record['num']} ─ #{getattr(reg_channel,'name','deleted-channel')}",
                    description=f"{record['team_name']} (ID: {record['scrim_id']})",
                    value=f"{record['scrim_id']}:{record['assigned_slot_id']}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder="Select slot(s) from this dropdown...", options=_options, max_values=len(records))

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        await interaction.response.defer()
        self.view.stop()
        self.view.custom_id = interaction.data["values"]
