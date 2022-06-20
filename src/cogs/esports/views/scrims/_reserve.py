from __future__ import annotations

import typing as T

import discord

from core import Context
from models import ReservedSlot, Scrim
from utils import string_input, truncate_string, QuoMember, BetterFutureTime

from ._base import ScrimsButton, ScrimsView
from ._btns import Discard
from ._pages import *

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
    view: ScrimsSlotReserve

    def __init__(self, ctx: Context):
        super().__init__(style=discord.ButtonStyle.green, label="Reserve Slot(s)")

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple(
            "Enter the slot details you want to reserve in the following format:\n"
            "> `slot_number`,`team_name`, `team_owner`, `time to reserve`\n\n"
            "Enter `none` in place of:\n"
            "- `team owner` if you want the slot be a management slot.\n"
            "- `time to reserve` if you want the reserve time to never expire.\n\n"
            "\n*don't forget to separate everything with comma (`,`)*\n",
            image="https://cdn.discordapp.com/attachments/851846932593770496/988408404341039134/reserve_help.gif",
        )

        slots = await string_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        if slots.strip().lower() == "cancel":
            return await self.ctx.error("Alright, Aborting.", 4)

        slots = slots.split("\n")
        for _ in slots:
            _ = _.split(",")

            try:
                num, team_name, team_owner, time_to_reserve = _
                num = int(num.strip())

                team_name = truncate_string(team_name.strip(), 25)

            except ValueError:
                return await self.ctx.error(
                    "The details you entered were not according to the proper format. Please refer to example image.", 6
                )

            owner_id = None
            if team_owner.strip().lower() != "none":
                owner = await QuoMember().convert(self.ctx, team_owner.strip())
                owner_id = owner.id

            expire = None
            if time_to_reserve.strip().lower() != "none":
                expire = await BetterFutureTime().convert(self.ctx, time_to_reserve.strip())

            if num not in (_range := self.view.record.available_to_reserve):
                return await self.error_embed(
                    f"The slot-number you entered (`{num}`) cannot be reserved.\n"
                    f"\nThe slot-number must be a number between `{_range.start}` and `{_range.stop}`",
                    5,
                )

            to_del = await self.view.record.reserved_slots.filter(num=num).first()
            if to_del:
                await ReservedSlot.filter(pk=to_del.id).delete()

            slot = await ReservedSlot.create(num=num, user_id=owner_id, team_name=team_name, expires=expire)
            await self.view.record.reserved_slots.add(slot)
            if expire and owner_id:
                await self.ctx.bot.reminders.create_timer(
                    expire, "scrim_reserve", scrim_id=self.view.record.id, user_id=owner_id, team_name=team_name, num=num
                )

        await self.view.refresh_view()


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
            await self.view.refresh_view()

        await self.ctx.safe_delete(m)


class SlotSelect(discord.ui.Select):
    view: ScrimsView

    def __init__(self, slots: T.List[ReservedSlot]):
        _options = []
        for _ in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Slot {_.num}",
                    description=f"Team: {_.team_name} ({_.leader or 'No leader'})",
                    value=_.id.__str__(),
                    emoji="<:menu:972807297812275220>",
                )
            )
        super().__init__(
            max_values=len(slots), placeholder="Select the slot(s) you want to remove from reserved", options=_options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = self.values
        self.view.stop()
