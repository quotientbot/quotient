from __future__ import annotations

import typing as T

import discord

from core import Context
from models import ReservedSlot, Scrim
from utils import string_input

from ._base import ScrimsView, ScrimsButton
from ._pages import *
from ._btns import Discard

__all__ = ("ScrimsSlotReserve",)


class ScrimsSlotReserve(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)

        self.ctx = ctx
        self.record = scrim

    @property
    async def initial_embed(self):
        _e = discord.Embed(color=self.bot.color)
        _e.description = f"**{self.record}  -  Reserved Slots**\n\n"

        reserved = await self.record.reserved_slots.order_by("num")
        _l = []
        for _ in range(self.record.start_from, self.record.total_slots + self.record.start_from):
            _l.append(f"Slot {_:02}  -->  " + next((i.team_name for i in reserved if i.num == _), "❌") + "\n")
        _e.description += f"```{''.join(_l)}```"
        _e.set_footer(text=f"Page - {' / '.join(await self.record.scrim_posi())}")
        return _e

    async def refresh_view(self):
        await self.add_buttons()
        try:
            self.message = await self.message.edit(embed=await self.initial_embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    async def add_buttons(self):
        self.clear_items()

        self.add_item(NewReserve(self.ctx))

        self.add_item(RemoveReserve(self.ctx, not bool(await self.record.reserved_slots.all().count())))

        if await Scrim.filter(guild_id=self.ctx.guild.id).count() >= 2:
            self.add_item(Prev(self.ctx, 2))
            self.add_item(SkipTo(self.ctx, 2))
            self.add_item(Next(self.ctx, 2))

        self.add_item(Discard(self.ctx, "Main Menu", 2))


class NewReserve(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(style=discord.ButtonStyle.green, label="Reserve Slot(s)")

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class RemoveReserve(ScrimsButton):
    def __init__(self, ctx: Context, disabled: bool = True):
        super().__init__(style=discord.ButtonStyle.red, label="Remove Reserved", disabled=disabled)

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        v = ScrimsView(self.ctx)
        v.add_item(SlotSelect(await self.view.record.reserved_slots.all().order_by("num")))

        m = await self.ctx.send("Please select the slots to remove from reserved:", view=v)
        await v.wait()

        if v.custom_id:
            await ReservedSlot.filter(id__in=v.custom_id).delete()
            await self.__refresh_view()

        await self.ctx.safe_delete(m)


class SlotSelect(discord.ui.Select):
    view: ScrimsView

    def __init__(self, slots: T.List[ReservedSlot]):
        _options = []
        for _ in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Slot {_.num}",
                    description=f"Team: {_.team_name} ({getattr(_.leader)})",
                    value=_.id.__str__(),
                    emoji="<:menu:972807297812275220>",
                )
            )
        super().__init__(max_values=len(slots), placeholder="Select the slot(s) you want to remove from reserved")

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = self.values
        self.view.stop()
