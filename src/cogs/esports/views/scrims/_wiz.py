from __future__ import annotations
import typing as T

from ._base import ScrimsView
from core import Context
from models import Scrim

from ._btns import *
import discord

__all__ = ("ScrimSetup",)


class ScrimSetup(ScrimsView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=60)

        self.ctx = ctx
        self.record: Scrim = None

        self.add_item(RegChannel(ctx, "a"))
        self.add_item(SlotChannel(ctx, "b"))
        self.add_item(SetRole(ctx, "c"))
        self.add_item(SetMentions(ctx, "d"))
        self.add_item(TotalSlots(ctx, "e"))
        self.add_item(OpenTime(ctx, "f"))
        self.add_item(SetEmojis(ctx, "g"))
        self.add_item(Discard(ctx, "Cancel"))
        self.add_item(SaveScrim(ctx))

    def initial_message(self):
        if not self.record:
            self.record = Scrim(guild_id=self.ctx.guild.id, host_id=self.ctx.author.id)

        d_link = "https://quotientbot.xyz/dashboard/{0}/scrims/create".format(self.ctx.guild.id)

        _e = discord.Embed()
        _e.description = f"[Scrim Creation is a piece of cake throug dashboard, Click Me]({d_link})\n\n"
        return _e

    async def refresh_view(self):
        _e = self.initial_message()

        if all(
            (
                self.record.registration_channel_id,
                self.record.slotlist_channel_id,
                self.record.role_id,
                self.record.required_mentions,
                self.record.total_slots,
                self.record.open_time,
            )
        ):
            self.children[-1].disabled = False

        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()
