from __future__ import annotations

import typing as T

import discord
from pydantic import BaseModel

import config
from core import Context
from core.embeds import EmbedBuilder
from models import Scrim
from utils import integer_input
from utils import keycap_digit as kd

from ._base import ScrimsView

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
        await self.scrim.refresh_from_db()

        from ._design import (BackBtn, MsgType, SaveMessageBtn, ScrimDesign,
                              SetDefault)

        if len(self.scrim.cdn["msg"]) <= 1:
            _e = ScrimDesign.default_countdown_msg()

        else:
            _e = discord.Embed.from_dict(self.scrim.cdn["msg"])

        self.stop()

        embed = discord.Embed(color=self.bot.color, title="Click Me if you need Help", url=self.bot.config.SERVER_LINK)
        embed.description = (
            f"\n*You are editing registration close message for {self.scrim}*\n\n"
            "**__Keywords you can use in design:__**\n"
            "`<<t>>` - Seconds left in opening reg (counter).\n"
        )
        await self.message.edit(embed=embed, content="", view=None)

        _v = EmbedBuilder(
            self.ctx,
            items=[
                SaveMessageBtn(self.ctx, self.scrim, MsgType.countdown, self.message),
                BackBtn(self.ctx, self.scrim, self.message),
                SetDefault(self.ctx, self.scrim, MsgType.countdown),
            ],
        )

        await _v.rendor(embed=_e)

    @discord.ui.button(style=discord.ButtonStyle.red, label="Back")
    async def go_back(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        from ._design import ScrimDesign

        self.stop()
        v = ScrimDesign(self.ctx, self.scrim)
        v.message = await self.message.edit(embed=v.initial_embed, view=v)
