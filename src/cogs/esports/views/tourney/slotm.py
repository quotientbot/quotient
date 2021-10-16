from __future__ import annotations

from ...views.base import EsportsBaseView

from models import Tourney, TMSlot

from core import Context

from utils import BaseSelector, Prompt

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
                    label=f"Number {slot.num} ── {slot.team_name.title()}",
                    description=f"Team: {', '.join((str(m) for m in map(bot.get_user, slot.members)))}",
                    value=slot.id,
                    emoji="<a:right_bullet:898869989648506921>",
                )
            )

        super().__init__(placeholder="Select a slot to Cancel", options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class TourneySlotManager(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney):
        super().__init__(ctx, timeout=None, title="Tourney Slot Manager")

        self.tourney = tourney
        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    def initial_embed() -> discord.Embed:
        embed = discord.Embed(
            color=config.COLOR,
            title="Cancel Tourney Slot",
            description=(
                "Click the red button below to cancel your slot for tourney_name.\n\n*Note that this action is irreversible.*",
            ),
        )
        return embed

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="cancel-slot", label="Cancel Your Slot")
    async def cancel_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        _slots = await self.tourney.assigned_slots.filter(members__contains=interaction.user.id)
        if not _slots:
            return await interaction.followup.send(
                embed=self.red_embed(f"You don't have any slot, because you haven't registered in {self.tourney} yet."),
                ephemeral=True,
            )

        cancel_view = BaseSelector(interaction.user.id, TCancelSlotSelector, bot=self.ctx.bot, slots=_slots)
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
                self.bot.loop.create_task(update_confirmed_message(self.ctx, self.tourney, slot, slot.confirm_jump_url))
