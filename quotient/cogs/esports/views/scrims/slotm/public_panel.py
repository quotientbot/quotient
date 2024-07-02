import logging
from typing import Any

import discord
from discord.ui.item import Item
from lib import BELL
from models import ScrimsSlotManager

from ..utility.selectors import ScrimsSlotSelector


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

        v = discord.ui.View()
        v.add_item(ScrimsSlotSelector(user_slots, multiple=True))
        v.message = await inter.followup.send(
            embed=self.record.bot.simple_embed("Please select the slots you want to cancel."),
            view=v,
            ephemeral=True,
        )

        await v.wait()
        await v.message.delete(delay=0)

        if not v.selected_slots:
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

        
        

    @discord.ui.button(label="Claim Slot", style=discord.ButtonStyle.green, custom_id="claim_scrims_slot")
    async def claim_scrims_slot(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

    @discord.ui.button(label="Remind Me", emoji=BELL)
    async def scrims_remind_me(self, inter: discord.Interaction, btn: discord.ui.Button, custom_id="scrims_slot_reminder"):
        await inter.response.defer()
