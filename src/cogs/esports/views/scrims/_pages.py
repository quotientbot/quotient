from __future__ import annotations

import discord

from core import Context
from models import Scrim

from ._base import ScrimsButton

__all__ = "Next", "Prev", "SkipTo"


class Next(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(emoji="<:double_right:878668437193359392>")
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _ids = [_.pk async for _ in Scrim.filter(guild_id=self.ctx.guild.id).order_by("open_time")]
        current = _ids.index(self.view.record.pk)

        try:
            next_id = _ids[current + 1]
        except IndexError:
            next_id = _ids[0]

        new_scrim = await Scrim.get(pk=next_id)
        if not self.view.record == new_scrim:
            self.view.record = new_scrim
            await self.view.refresh_view()


class Prev(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(emoji="<:double_left:878668594530099220>")
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _ids = [_.pk async for _ in Scrim.filter(guild_id=self.ctx.guild.id).order_by("open_time")]
        current = _ids.index(self.view.record.pk)

        try:
            next_id = _ids[current - 1]
        except IndexError:
            next_id = _ids[-1]

        new_scrim = await Scrim.get(pk=next_id)
        if not self.view.record == new_scrim:
            self.view.record = new_scrim
            await self.view.refresh_view()


class SkipTo(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(label="Skip to...")
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
