import logging
import re
from typing import Any

import discord
from discord.ui.item import Item
from lib import BELL, LOADING
from models import Scrim, ScrimAssignedSlot, ScrimsSlotManager

from ..utility.selectors import ScrimsSlotSelector, prompt_scrims_slot_selector


class TeamNameInput(discord.ui.Modal, title="Slot Claim Form"):
    team_name = discord.ui.TextInput(label="Enter your team name:", min_length=3, max_length=20)

    async def on_submit(self, inter: discord.Interaction):
        await inter.response.defer()


class ScrimSlotmPublicPanel(discord.ui.View):
    def __init__(self, record: ScrimsSlotManager):
        super().__init__(timeout=None)
        self.record = record

    async def on_error(self, interaction: discord.Interaction[discord.Client], error: Exception, item: Item[Any]) -> None:
        if isinstance(error, discord.NotFound):
            return
        logging.error(f"Error in {self.__class__.__name__}: {error}")

    @discord.ui.button(label="Cancel Slot", style=discord.ButtonStyle.red, custom_id="cancel_scrims_slot")
    async def cancel_scrims_slot(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer(thinking=True, ephemeral=True)

        if not (user_slots := await self.record.get_user_slots(inter.user.id)):
            return await inter.followup.send(
                embed=self.record.bot.error_embed("You don't have any slots that can be cancelled."), ephemeral=True
            )

        selected_slots = await prompt_scrims_slot_selector(
            inter, user_slots, "Please select the slots you want to cancel from dropdown.", multiple=True
        )
        if not selected_slots:
            return

        prompt = await self.record.bot.prompt(
            inter,
            inter.user,
            "Are you sure you want to cancel the selected slots?",
            msg_title="This action can't be undone!",
            confirm_btn_label="Yes",
            cancel_btn_label="No, Cancel",
            ephemeral=True,
        )
        if not prompt:
            return

        m = await inter.followup.send(f"Please wait, cancelling selected slots {LOADING}", ephemeral=True)

        for slot in selected_slots:
            slot.scrim.available_slots.append(slot.num)
            slot.scrim.available_slots = sorted(slot.scrim.available_slots)
            await slot.scrim.save(update_fields=["available_slots"])
            await slot.delete()

            slot.bot.loop.create_task(slot.scrim.refresh_slotlist_message())

            await self.record.dispatch_reminders(slot.scrim.id)

        await m.edit(content="Selected slots have been cancelled successfully.", embed=None, view=None)
        await self.record.refresh_public_message()

        cancelled_slots = ""
        for slot in selected_slots:
            cancelled_slots += f"- Slot {slot.num} - {slot.scrim}\n"

        await slot.scrim.send_log(
            msg=f"Scrims Slots Cancelled by {inter.user.mention} through Cancel-Claim Panel:\n{cancelled_slots}",
            title="Scrims Slot Cancelled",
            color=discord.Color.red(),
            add_contact_btn=False,
        )

    @discord.ui.button(label="Claim Slot", style=discord.ButtonStyle.green, custom_id="claim_scrims_slot")
    async def claim_scrims_slot(self, inter: discord.Interaction, btn: discord.ui.Button):
        m = TeamNameInput()
        await inter.response.send_modal(m)
        await m.wait()
        team_name = "Team " + re.sub(r"team|name|[^\w\s]", "", m.team_name.lower()).strip().title()

        available_scrims = await self.record.claimable_scrims()
        if not available_scrims:
            return await inter.followup.send(embed=self.record.bot.error_embed("No slots available to claim."), ephemeral=True)

    @discord.ui.button(label="Remind Me", emoji=BELL, custom_id="scrims_slot_reminder")
    async def scrims_remind_me(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()
