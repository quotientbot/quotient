from __future__ import annotations

import typing as T
from ._base import ScrimsView
import discord

from models import Scrim

from core import Context
from utils import regional_indicator as ri


class ScrimDesign(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx, timeout=60.0)

        self.scrim = scrim
        self.ctx = ctx

    @property
    def intial_embed(self):
        _e = discord.Embed(color=0x00FFB3)
        _e.description = (
            f"[**Scrims - Design Settings - {self.scrim}**]({self.ctx.config.SERVER_LINK})\n"
            "What do you want to design today?\n\n"
            f"{ri('a')} - Registration Open Message\n"
            f"{ri('b')} - Registration Close Message\n"
            f"{ri('c')} - Registratipn Open Countdown\n"
            f"{ri('d')} - Slotlist Design\n"
        )
        return _e

    @discord.ui.button(emoji=ri("a"))
    async def reg_open_message(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(emoji=ri("b"))
    async def reg_clse_message(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(emoji=ri("c"))
    async def pre_reg_msg(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(emoji=ri("d"))
    async def slotlist_design(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()
