import discord
from discord.ext import commands
from lib import NEXT_PAGE, PREVIOUS_PAGE, integer_input_modal

from quotient.models import Scrim

from ...scrims import ScrimsBtn


class NextScrim(ScrimsBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx=ctx, emoji=NEXT_PAGE, row=row, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")

        current_scrim_index = [scrim.pk for scrim in all_scrims].index(self.view.record.pk)

        try:
            next_scrim = all_scrims[current_scrim_index + 1]
        except IndexError:
            next_scrim = all_scrims[0]

        if not self.view.record.pk == next_scrim.pk:
            self.view.record = next_scrim
            await self.view.refresh_view()


class SkipToScrim(ScrimsBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx, label="Skip to...", row=row)

    async def callback(self, interaction: discord.Interaction):

        scrim_position = await integer_input_modal(
            inter=interaction,
            title="Skip to Page",
            label="Please enter the page no.",
        )

        all_scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")

        if not scrim_position:
            return

        if scrim_position > len(all_scrims):
            return await interaction.followup.send("Invalid page number. Please try again.", ephemeral=True)

        self.view.record = all_scrims[scrim_position - 1]
        await self.view.refresh_view()


class PreviousScrim(ScrimsBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx=ctx, emoji=PREVIOUS_PAGE, row=row, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")

        current_scrim_index = [scrim.pk for scrim in all_scrims].index(self.view.record.pk)

        try:
            prev_scrim = all_scrims[current_scrim_index - 1]
        except IndexError:
            prev_scrim = all_scrims[-1]

        if not self.view.record.pk == prev_scrim.pk:
            self.view.record = prev_scrim
            await self.view.refresh_view()
