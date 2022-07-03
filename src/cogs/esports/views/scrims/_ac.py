from __future__ import annotations

import typing as T

import discord

from constants import AutocleanType
from core import Context
from models import ArrayAppend, ArrayRemove, Scrim, Timer
from utils import keycap_digit as kd
from utils import time_input

from ._base import ScrimsButton, ScrimsView
from ._pages import *

__all__ = ("AutocleanView",)


class AutocleanView(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)
        self.ctx = ctx
        self.record = scrim

    @property
    async def initial_embed(self) -> discord.Embed:
        autoclean_time = (self.record.autoclean_time).strftime("%I:%M %p") if self.record.autoclean_time else "Not Set!"

        _e = discord.Embed(color=self.ctx.bot.color, description=f"**Scrim Autoclean - {self.record}**\n")
        _d = "\n".join(
            f"{idx:02}. {(_type.value.title()).ljust(15)} {('❌', '✅')[_type in self.record.autoclean]}"
            for idx, _type in enumerate(AutocleanType, start=1)
        )

        _e.description += f"```{_d}```\n"
        _e.description += f"```03. Clean At: {autoclean_time}```"
        _e.set_footer(text=f"Page - {' / '.join(await self.record.scrim_posi())}")

        return _e

    async def refresh_view(self):
        await self.record.refresh_from_db()

        await self._add_buttons()
        try:
            self.message = await self.message.edit(embed=await self.initial_embed)
        except discord.HTTPException:
            await self.on_timeout()

    async def _add_buttons(self):
        self.clear_items()

        self.add_item(OnOne())
        self.add_item(OnTwo())
        self.add_item(OnThree())
        if await Scrim.filter(guild_id=self.ctx.guild.id).count() >= 2:
            self.add_item(Prev(self.ctx, 2))
            self.add_item(SkipTo(self.ctx, 2))
            self.add_item(Next(self.ctx, 2))

        self.add_item(Back())


class OnOne(ScrimsButton):
    def __init__(self):
        super().__init__(emoji=kd(1))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        func = (ArrayAppend, ArrayRemove)[AutocleanType.channel in self.view.record.autoclean]
        await Scrim.filter(pk=self.view.record.id).update(autoclean=func("autoclean", AutocleanType.channel))
        await self.view.refresh_view()

        await self.view.ctx.success(
            f"Registration channel will {('not be','be')[AutocleanType.channel in self.view.record.autoclean]} autocleaned.",
            4,
        )


class OnTwo(ScrimsButton):
    def __init__(self):
        super().__init__(emoji=kd(2))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        func = (ArrayAppend, ArrayRemove)[AutocleanType.role in self.view.record.autoclean]
        await Scrim.filter(pk=self.view.record.id).update(autoclean=func("autoclean", AutocleanType.role))
        await self.view.refresh_view()

        await self.view.ctx.success(
            f"Scrim role will {('not be','be')[AutocleanType.role in self.view.record.autoclean]} removed from everyone.",
            4,
        )


class OnThree(ScrimsButton):
    def __init__(self):
        super().__init__(emoji=kd(3))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        m = await self.view.ctx.simple(
            "At what time do you want me to run autoclean?\n\nTime examples:",
            image="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
            footer="Time is according to Indian Standard Time (UTC+05:30)",
        )
        t = await time_input(self.view.ctx, delete_after=True)
        await self.view.ctx.safe_delete(m)
        self.view.record.autoclean_time = t
        
        await Timer.filter(extra={"args": [], "kwargs": {"scrim_id": self.view.record.id}}, event="autoclean").delete()

        await self.view.bot.reminders.create_timer(t, "autoclean", scrim_id=self.view.record.id)

        await self.view.record.make_changes(autoclean_time=t)
        await self.view.refresh_view()


class Back(ScrimsButton):
    def __init__(self):
        super().__init__(label="Back", style=discord.ButtonStyle.red, row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        from ._edit import ScrimsEditor

        v = ScrimsEditor(self.view.ctx, self.view.record)
        await v._add_buttons()
        v.message = await self.view.message.edit(embed=await v.initial_message, view=v)
