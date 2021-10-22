from __future__ import annotations

from models import Tourney, TMSlot

from utils import BaseSelector, Prompt, emote

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from ...helpers import update_confirmed_message

import config
import discord


class TCancelSlotSelector(discord.ui.Select):
    def __init__(self, bot: Quotient, slots: List[TMSlot]):

        _options = []
        for slot in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Number {slot.num} ─ {slot.team_name.title()}",
                    description=f"Team: {', '.join((str(m) for m in map(bot.get_user, slot.members)))}",
                    value=slot.id,
                    emoji="<a:right_bullet:898869989648506921>",
                )
            )

        super().__init__(placeholder="Select a slot to Cancel", options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class TourneySlotManager(discord.ui.View):
    def __init__(self, bot: Quotient, *, tourney: Tourney):

        self.tourney = tourney
        self.bot = bot
        self.title = "Tourney Slot Manager"
        super().__init__(timeout=None)

    def red_embed(self, description: str) -> discord.Embed:
        return discord.Embed(color=discord.Color.red(), title=self.title, description=description)

    @staticmethod
    def initial_embed(tourney: Tourney) -> discord.Embed:
        embed = discord.Embed(
            color=config.COLOR,
            description=(
                f"**[Tourney Slot Manager]({config.SERVER_LINK})** ─ {tourney}\n\n"
                f"• Click `Cancel My Slot` below to cancel your slot.\n"
                "• Click `My Slots` to get info about all your slots.\n\n"
                "*Note that slot cancel is irreversible.*"
            ),
        )
        return embed

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="tourney-cancel-slot", label="Cancel My Slot")
    async def cancel_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        _slots = await self.tourney.assigned_slots.filter(members__contains=interaction.user.id).order_by("num")
        if not _slots:
            return await interaction.followup.send(
                embed=self.red_embed(f"You don't have any slot, because you haven't registered in {self.tourney} yet."),
                ephemeral=True,
            )

        cancel_view = BaseSelector(interaction.user.id, TCancelSlotSelector, bot=self.bot, slots=_slots)
        await interaction.followup.send("Kindly choose one of the following slots", view=cancel_view, ephemeral=True)

        await cancel_view.wait()

        if _id := cancel_view.custom_id:

            prompt = Prompt(interaction.user.id)
            await interaction.followup.send("Are you sure you want to cancel your slot?", view=prompt, ephemeral=True)
            await prompt.wait()

            if not prompt.value:
                return await interaction.followup.send("Alright, Aborting.", ephemeral=True)

            slot = await TMSlot.get_or_none(pk=_id)
            if not slot:
                return await interaction.followup.send(embed=self.red_embed("Slot is already deleted."), ephemeral=True)

            if slot.confirm_jump_url:
                self.bot.loop.create_task(update_confirmed_message(self.tourney, slot.confirm_jump_url))

            if len(_slots) == 1:
                self.bot.loop.create_task(interaction.user.remove_roles(self.tourney.role))

            await slot.delete()
            return await interaction.followup.send(f"{emote.check} | Your slot was removed.",ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="tourney-slot-info", label="My Slots")
    async def _slots_info(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        _slots = await self.tourney.assigned_slots.filter(members__contains=interaction.user.id).order_by("num")
        if not _slots:
            return await interaction.followup.send(
                embed=self.red_embed(f"You don't have any slot, because you haven't registered in {self.tourney} yet."),
                ephemeral=True,
            )

        embed = discord.Embed(color=config.COLOR)
        embed.description = f"Your have the following slots in {self.tourney}:\n\n"

        for idx, slot in enumerate(_slots, start=1):
            embed.description += (
                f"**[`{idx}.`]({config.SERVER_LINK}) {slot.team_name.title()} ([Slot {slot.num}]({slot.jump_url}))**\n"
            )

        return await interaction.followup.send(embed=embed, ephemeral=True)
