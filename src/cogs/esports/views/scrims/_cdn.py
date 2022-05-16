from __future__ import annotations

import typing as T
from ._base import ScrimsView
from core import Context
from models import Scrim

import discord
from pydantic import BaseModel

from utils import keycap_digit as kd, integer_input

__all__ = ("ScrimsCDN",)


class CDN(BaseModel):
    status: bool = False
    countdown: int = 5
    msg: dict = ...


class ScrimsCDN(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx, timeout=60.0)

        self.scrim = scrim

    @property
    def initial_embed(self):
        _e = discord.Embed(color=self.bot.color)

    async def refresh_view(self, **kwargs):
        ...

    @discord.ui.button(emoji=kd(1))
    async def change_status(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        self.scrim.cdn["status"] = not self.scrim.cdn["status"]
        await self.refresh_view(cdn=self.scrim.cdn)

    @discord.ui.button(emoji=kd(2))
    async def set_time(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        _m = await self.ctx.simple("How many seconds should the countdown be? (Min: `3` Max: `10`)")
        self.scrim.cdn["countdown"] = await integer_input(self.ctx, limits=(3, 10))

        await self.refresh_view(cdn=self.scrim.cdn)

    @discord.ui.button(emoji=kd(3))
    async def set_msg(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()
