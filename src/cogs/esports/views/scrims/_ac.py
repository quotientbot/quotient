from __future__ import annotations

import typing as T

import discord

from constants import AutocleanType
from core import Context
from models import ArrayAppend, ArrayRemove, Scrim
from utils import keycap_digit as kd
from utils import time_input

from ._base import EsportsBaseView

__all__ = ("AutocleanView",)


class AutocleanView(EsportsBaseView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)
        self.ctx = ctx
        self.scrim = scrim

    @property
    def initial_embed(self) -> discord.Embed:
        autoclean_time = (self.scrim.autoclean_time).strftime("%I:%M %p") if self.scrim.autoclean_time else "Not Set!"

        _e = discord.Embed(color=self.ctx.bot.color, description=f"**Scrim Autoclean - {self.scrim}**\n")
        _d = "\n".join(
            f"{idx:02}. {(_type.value.title()).ljust(15)} {('❌', '✅')[_type in self.scrim.autoclean]}"
            for idx, _type in enumerate(AutocleanType, start=1)
        )

        _e.description += f"```{_d}```\n"
        _e.description += f"```03. Clean At: {autoclean_time}```"

        return _e

    async def refresh_view(self):
        await self.scrim.refresh_from_db()
        await self.message.edit(embed=self.initial_embed)

    @discord.ui.button(emoji=kd(1))
    async def on_one(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()
        func = (ArrayAppend, ArrayRemove)[AutocleanType.channel in self.scrim.autoclean]
        await Scrim.filter(pk=self.scrim.id).update(autoclean=func("autoclean", AutocleanType.channel))
        await self.refresh_view()

        await self.ctx.success(
            f"Registration channel will {('not be','be')[AutocleanType.channel in self.scrim.autoclean]} autocleaned.", 4
        )

    @discord.ui.button(emoji=kd(2))
    async def on_two(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()
        func = (ArrayAppend, ArrayRemove)[AutocleanType.role in self.scrim.autoclean]
        await Scrim.filter(pk=self.scrim.id).update(autoclean=func("autoclean", AutocleanType.role))
        await self.refresh_view()

        await self.ctx.success(
            f"Scrim role will {('not be','be')[AutocleanType.role in self.scrim.autoclean]} removed from everyone.", 4
        )

    @discord.ui.button(emoji=kd(3))
    async def on_three(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

        m = await self.ctx.simple(
            "At what time do you want me to run autoclean?\n\nTime examples:",
            image="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
            footer="Time is according to Indian Standard Time (UTC+05:30)",
        )
        t = await time_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)
        self.scrim.autoclean_time = t

        await self.scrim.make_changes(autoclean_time=t)
        await self.refresh_view()

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red)
    async def go_back(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()
