from __future__ import annotations

import typing as T
from ._base import ScrimsView
from core import Context
from models import Scrim

import discord
from pydantic import BaseModel


class CDN(BaseModel):
    status: bool = False
    countdown: int = 5
    msg:dict = ...


class ScrimsCDN(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx, timeout=60.0)

        self.scrim = scrim

    @property
    def initial_embed(self):
        _e = discord.Embed(color=self.bot.color)

    @discord.ui.button()
    async def change_status(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button()
    async def set_time(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button()
    async def set_msg(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()
