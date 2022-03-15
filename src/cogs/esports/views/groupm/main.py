from __future__ import annotations
from contextlib import suppress

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from ..base import EsportsBaseView
from core import Context

from models import Tourney

from utils import keycap_digit, inputs

__all__ = ("TourneyGroupManager",)


class TourneyGroupManager(EsportsBaseView):
    def __init__(self, ctx: Context, tourney: Tourney, **kwargs):
        super().__init__(ctx, **kwargs)

        self.tourney = tourney

        self.start_from = tourney.slotlist_start

    @property
    def initial_embed(self):
        _e = discord.Embed(
            color=self.ctx.bot.color, title="Tourney Group Management", url=self.tourney.bot.config.SERVER_LINK
        )
        _e.description = (
            f"Use `create channels & roles` to setup tourney groups.\n"
            "Use `Group List` to post group/slotlist in channels."
        )
        _e.add_field(name=f"{keycap_digit(1)} Slotlist Start from", value=f"`Slot {self.start_from}`")
        _e.add_field(name=f"{keycap_digit(2)} Ping Group Role", value=("`No!`", "`Yes!`")[self.ping_role])
        return _e

    async def __refresh_msg(self):
        with suppress(discord.HTTPException):
            self.message = await self.message.edit(embed=self.initial_embed)

    @discord.ui.button(emoji=keycap_digit(1))
    async def change_slotlist_start(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("Enter the slot number to start group/slotlist. (Max `20`)")
        self.start_from = await inputs.integer_input(self.ctx, limits=(1, 20), delete_after=True)
        await self.ctx.safe_delete(m)

        await self.tourney.make_changes(slotlist_start=self.start_from)

        await self.__refresh_msg()

    @discord.ui.button(label="Create Channels & Roles")
    async def create_roles_channels(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        _e = discord.Embed(color=0x00FFB3)
        _e.description = (
            "Enter the format for group roles & channels creation.\n"
            "*{0} will be replaced by the number of group or roles*\n\nExamples:"
        )

    @discord.ui.button(label="Group List", style=discord.ButtonStyle.green)
    async def send_grouplist(self, button: discord.Button, interaction: discord.Interaction):
        ...
