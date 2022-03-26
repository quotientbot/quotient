from __future__ import annotations
import typing as T

from ...views.base import EsportsBaseView
from core import Context

from discord import ButtonStyle, ui, Interaction
import discord

from ._wiz import ScrimSetup


class ScrimsMain(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100)

        self.ctx = ctx

    async def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3, description="hi bro")

        return _e

    @discord.ui.button(label="Create Scrim", style=ButtonStyle.green)
    async def create_new_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        if not await self.ctx.is_premium_guild():
            ...

        v = ScrimSetup(self.ctx)
        v.message = await self.message.edit(embed=v.initial_message(), view=v)

    @discord.ui.button(label="Edit Settings", style=ButtonStyle.blurple)
    async def edit_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Start/Stop Reg", style=ButtonStyle.green)
    async def toggle_reg(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Reserve Slots", style=ButtonStyle.green)
    async def reserve_slots(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Ban/Unban", style=ButtonStyle.red)
    async def ban_unban(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Design", style=ButtonStyle.red)
    async def change_design(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

    @discord.ui.button(label="Design", style=ButtonStyle.red)
    async def change_design(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()
