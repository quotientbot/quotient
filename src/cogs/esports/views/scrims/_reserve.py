from __future__ import annotations
import typing as T
from ._base import ScrimsView

from core import Context
from models import Scrim
import discord


class ScrimsSlotReserve(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)

        self.ctx = ctx
        self.scrim = scrim

    @discord.ui.button(style=discord.ButtonStyle.green, label="Reserve Slot(s)")
    async def reserve(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Reserved")
    async def unreserve(self, btn: discord.Button, inter: discord.Interaction):  # no idea if unreserve is a word lol
        await inter.response.defer()
