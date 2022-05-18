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
        _e = discord.Embed(
            color=self.bot.color,
        )
        _e.description = "**Registration open countdown editor -** {0}".format(self.scrim)

        fields = {
            "ON / OFF": ("`OFF`", "`ON`")[self.scrim.cdn["status"]],
            "Countdown": f"`{self.scrim.cdn['countdown']}s`",
            "Message": "`Click to view or edit`",
        }

        for idx, (name, value) in enumerate(fields.items(), 1):
            _e.add_field(
                name=f"{kd(idx)} {name}:",
                value=value,
                inline=False,
            )

        return _e

    async def refresh_view(self, **kwargs):
        await self.scrim.make_changes(**kwargs)
        self.message = await self.message.edit(embed=self.initial_embed, view=self)

    @discord.ui.button(emoji=kd(1))
    async def change_status(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        self.scrim.cdn["status"] = not self.scrim.cdn["status"]
        await self.refresh_view(cdn=self.scrim.cdn)

    @discord.ui.button(emoji=kd(2))
    async def set_time(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        _m = await self.ctx.simple("How many seconds should the countdown be? (Min: `3` Max: `10`)")
        self.scrim.cdn["countdown"] = await integer_input(self.ctx, limits=(3, 10), delete_after=True)
        await self.ctx.safe_delete(_m)
        await self.refresh_view(cdn=self.scrim.cdn)

    @discord.ui.button(emoji=kd(3))
    async def set_msg(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Back")
    async def go_back(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        from ._design import ScrimDesign

        self.stop()
        v = ScrimDesign(self.ctx, self.scrim)
        v.message = await self.message.edit(embed=v.initial_embed, view=v)
