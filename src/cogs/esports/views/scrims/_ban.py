from __future__ import annotations

from ._base import ScrimsButton, ScrimsView
from core import Context
from models import Scrim
import discord

from ._btns import Discard
from ._pages import *

__all__ = ("ScrimBanManager",)


class ScrimBanManager(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)

        self.ctx = ctx
        self.record = scrim

    @property
    async def initial_message(self):
        _e = discord.Embed(color=self.bot.color)

        _e.set_footer(text=f"Page - {' / '.join(await self.record.scrim_posi())}")
        return _e

    async def refresh_view(self):
        await self._add_buttons()
        try:
            self.message = await self.message.edit(embed=await self.initial_message, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    async def _add_buttons(self):
        self.clear_items()

        self.add_item(Ban())
        self.add_item(UnBan())

        if await Scrim.filter(guild_id=self.ctx.guild.id).count() >= 2:
            self.add_item(Prev(self.ctx, 2))
            self.add_item(SkipTo(self.ctx, 2))
            self.add_item(Next(self.ctx, 2))

        self.add_item(Discard(self.ctx, "Main Menu", 2))


class Ban(ScrimsButton):
    def __init__(self):
        super().__init__(label="Ban Users", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class UnBan(ScrimsButton):
    def __init__(self):
        super().__init__(label="UnBan Users", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
