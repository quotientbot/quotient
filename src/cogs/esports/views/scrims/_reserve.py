from __future__ import annotations

import typing as T

import discord

from core import Context
from models import ReservedSlot, Scrim
from utils import string_input

from ._base import ScrimsView


class ScrimsSlotReserve(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx)

        self.ctx = ctx
        self.scrim = scrim

    async def __refresh_view(self):
        ...

    @discord.ui.button(style=discord.ButtonStyle.green, label="Reserve Slot(s)")
    async def reserve(self, btn: discord.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Reserved")
    async def unreserve(self, btn: discord.Button, inter: discord.Interaction):  # no idea if unreserve is a word lol
        await inter.response.defer()

        v = ScrimsView(self.ctx)
        v.add_item(SlotSelect(await self.scrim.reserved_slots.all().order_by("num")))
        await v.wait()
        if v.custom_id:
            await ReservedSlot.filter(id__in=v.custom_id).delete()
            await self.__refresh_view()


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
