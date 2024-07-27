import discord
from cogs.esports.views.tourney import TourneyBtn
from discord.ext import commands
from lib import NEXT_PAGE, PREVIOUS_PAGE, integer_input_modal
from models import Tourney


class NextTourney(TourneyBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx=ctx, emoji=NEXT_PAGE, row=row, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_tourneys = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id")

        current_tourney_index = [tourney.pk for tourney in all_tourneys].index(self.view.record.pk)

        try:
            next_tourney = all_tourneys[current_tourney_index + 1]
        except IndexError:
            next_tourney = all_tourneys[0]

        if not self.view.record.pk == next_tourney.pk:
            self.view.record = next_tourney
            await self.view.refresh_view()


class SkipToTourney(TourneyBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx, label="Skip to...", row=row)

    async def callback(self, interaction: discord.Interaction):

        tourney_position = await integer_input_modal(
            inter=interaction,
            title="Skip to Page",
            label="Please enter the page no.",
        )

        all_tourneys = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id")

        if not tourney_position:
            return

        if tourney_position > len(all_tourneys):
            return await interaction.followup.send("Invalid page number. Please try again.", ephemeral=True)

        self.view.record = all_tourneys[tourney_position - 1]
        await self.view.refresh_view()


class PreviousTourney(TourneyBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx=ctx, emoji=PREVIOUS_PAGE, row=row, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_tourneys = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id")

        current_tourney_index = [tourney.pk for tourney in all_tourneys].index(self.view.record.pk)

        try:
            prev_tourney = all_tourneys[current_tourney_index - 1]
        except IndexError:
            prev_tourney = all_tourneys[-1]

        if not self.view.record.pk == prev_tourney.pk:
            self.view.record = prev_tourney
            await self.view.refresh_view()
