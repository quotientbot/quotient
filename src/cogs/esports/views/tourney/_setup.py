from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Context
from ...views.base import EsportsBaseView

import discord


class TourneyManager(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100, name="Tourney Manager")

    async def initial_embed(self) -> discord.Embed:
        _e = discord.Embed(color=self.bot.color)

        return _e

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="create_tourney", label="Create Tournament")
    async def create_tournament(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="edit_tourney", label="Edit Settings")
    async def edit_tournament(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()  