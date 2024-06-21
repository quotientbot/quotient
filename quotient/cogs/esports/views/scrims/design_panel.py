import discord
from discord.ext import commands
from lib import EXIT, regional_indicator
from models import Scrim

from . import ScrimsBtn, ScrimsView
from .utility.buttons import DiscardChanges
from .utility.common import get_scrim_position
from .utility.paginator import NextScrim, PreviousScrim, SkipToScrim


class ScrimsDesignPanel(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx, timeout=100)
        self.record = scrim

    async def initial_msg(self) -> discord.Embed:
        scrims = await Scrim.filter(guild_id=self.record.guild_id).order_by("reg_start_time")

        self.clear_items()

        self.add_item(EditOpenMsg(self.ctx))
        self.add_item(EditCloseMsg(self.ctx))
        self.add_item(EditSlotlistMsg(self.ctx))

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx, row=2))
            self.add_item(SkipToScrim(self.ctx, row=2))
            self.add_item(NextScrim(self.ctx, row=2))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT, row=2))

        e = discord.Embed(color=0x00FFB3)
        e.description = f"**{self.record} - Design Settings**\n"

        e.description += (
            "What do you want to design today?\n\n"
            f"{regional_indicator('a')} - Registration Open Message\n"
            f"{regional_indicator('b')} - Registration Close Message\n"
            f"{regional_indicator('c')} - Slotlist Design\n"
        )

        e.set_footer(text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.record.guild_id))}")
        return e

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()


class EditOpenMsg(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, emoji=regional_indicator("A"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()


class EditCloseMsg(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, emoji=regional_indicator("B"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()


class EditSlotlistMsg(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, emoji=regional_indicator("C"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()
