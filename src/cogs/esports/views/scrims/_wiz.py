from __future__ import annotations
import typing as T

from ._base import ScrimsView
from core import Context
from models import Scrim

from string import ascii_uppercase
from ._btns import *
import discord
from utils import discord_timestamp as dt

__all__ = ("ScrimSetup",)

# TODO: adjust open days in setup wizard
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

        self.add_item(OpenDays(ctx, "g"))
        self.add_item(SetEmojis(ctx, "h"))
        self.add_item(Discard(ctx, "Cancel"))
        self.add_item(SaveScrim(ctx))

    def initial_message(self):
        if not self.record:
            self.record = Scrim(guild_id=self.ctx.guild.id, host_id=self.ctx.author.id)

        d_link = "https://quotientbot.xyz/dashboard/{0}/scrims/create".format(self.ctx.guild.id)

        _e = discord.Embed(color=0x00FFB3, title="Enter details & Press Save", url=self.bot.config.SERVER_LINK)
        _e.description = f"[`Scrim Creation is a piece of cake through dashboard, Click Me`]({d_link})\n\n"

        fields = {
            "Reg. Channel": getattr(self.record.registration_channel, "mention", "`Not-Set`"),
            "Slotlist Channel": getattr(self.record.slotlist_channel, "mention", "`Not-Set`"),
            "Success Role": getattr(self.record.role, "mention", "`Not-Set`"),
            "Req. Mentions": f"`{self.record.required_mentions}`",
            "Total Slots": f"`{self.record.total_slots or 'Not-Set'}`",
            "Open Time": f"{dt(self.record.open_time,'t')} ({dt(self.record.open_time)})"
            if self.record.open_time
            else "`Not-Set`",
            "Scrim Days": ", ".join(map(lambda x: "`{0}`".format(x.name.title()[:2]), self.record.open_days)),
            f"Reactions {self.bot.config.PRIME_EMOJI}": f"{self.record.check_emoji},{self.record.cross_emoji}",
        }

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )
        _e.add_field(name="\u200b", value="\u200b")
        _e.set_footer(
            text="Quotient Premium servers can set custom reactions.", icon_url=self.ctx.guild.me.display_avatar.url
        )

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
