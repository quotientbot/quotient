import discord
from discord.ext import commands
from discord.utils import format_dt
from lib import DIAMOND, keycap_digit
from models import Scrim

from ..scrims import ScrimsView
from .utility.buttons import (
    DiscardChanges,
    SaveScrim,
    SetMentions,
    SetReactions,
    SetRegChannel,
    SetRegOpenDays,
    SetRegStartTime,
    SetTotalSlots,
)


class CreateScrimView(ScrimsView):

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

        self.record: Scrim = None

        self.add_item(SetRegChannel(ctx, keycap_digit(1)))
        self.add_item(SetMentions(ctx, keycap_digit(2)))
        self.add_item(SetTotalSlots(ctx, keycap_digit(3)))
        self.add_item(SetRegStartTime(ctx, keycap_digit(4)))
        self.add_item(SetRegOpenDays(ctx, keycap_digit(5)))
        self.add_item(SetReactions(ctx, keycap_digit(6)))
        self.add_item(DiscardChanges(ctx, label="Discard"))
        self.add_item(SaveScrim(ctx))

    def initial_msg(self):
        if not self.record:
            self.record = Scrim(guild_id=self.ctx.guild.id)

        e = discord.Embed(
            color=self.bot.color, title="Enter details & Press Create Scrim", url=self.bot.config("SUPPORT_SERVER_LINK")
        )

        e.description = "`You can skip this step & quickly create scrims using '/scrims create' command.`\n\n"

        fields = {
            "Reg. Channel": getattr(self.record.registration_channel, "mention", "`Not Set`"),
            "Req. Mentions": f"`{self.record.required_mentions}`",
            "Total Slots": f"`{self.record.total_slots or 'Not-Set'}`",
            "Reg Start Time": (
                f"{format_dt(self.record.reg_start_time,'t')} ({format_dt(self.record.reg_start_time)})"
                if self.record.reg_start_time
                else "`Not Set`"
            ),
            "Scrim Days": f"`{self.record.pretty_registration_days}`",
            f"Reactions {DIAMOND}": f"{self.record.reactions[0]}, {self.record.reactions[1]}",
        }

        for idx, (name, value) in enumerate(fields.items(), start=1):
            e.add_field(
                name=f"{keycap_digit(idx)} {name}:",
                value=value,
            )
        # e.add_field(name="\u200b", value="\u200b")
        e.set_footer(text="Quotient Pro servers can set custom reactions.", icon_url=self.ctx.guild.me.display_avatar.url)
        return e

    async def refresh_view(self):
        _e = self.initial_msg()

        if all(
            (
                self.record.registration_channel_id,
                self.record.total_slots,
                self.record.reg_start_time,
                self.record.registration_open_days,
            )
        ):
            self.children[-1].disabled = False

        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()
