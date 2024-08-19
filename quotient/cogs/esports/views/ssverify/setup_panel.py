import discord
from discord.ext import commands

from quotient.lib import keycap_digit
from quotient.models import SSverify

from . import SsVerifyView
from .utility.buttons import (
    DiscardButton,
    SaveButton,
    SetAllowDuplicateSS,
    SetEntityLink,
    SetEntityName,
    SetRegChannel,
    SetRequiredSS,
    SetScreenshotType,
    SetSuccessRole,
)


class CreateSsVerify(SsVerifyView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

        self.record = SSverify(guild_id=ctx.guild.id)

    def initial_msg(self) -> discord.Embed:

        self.clear_items()

        self.add_item(SetRegChannel(self.ctx, keycap_digit(1)))
        self.add_item(SetSuccessRole(self.ctx, keycap_digit(2)))
        self.add_item(SetRequiredSS(self.ctx, keycap_digit(3)))
        self.add_item(SetScreenshotType(self.ctx, keycap_digit(4)))
        self.add_item(SetEntityName(self.ctx, keycap_digit(5)))
        self.add_item(SetEntityLink(self.ctx, keycap_digit(6)))
        self.add_item(SetAllowDuplicateSS(self.ctx, keycap_digit(7)))
        self.add_item(DiscardButton(self.ctx))
        self.add_item(SaveButton(self.ctx))

        e = discord.Embed(
            color=self.bot.color, title="Enter details & Press Setup SsVerify", url=self.bot.config("SUPPORT_SERVER_LINK")
        )

        fields = {
            "Channel": getattr(self.record.channel, "mention", "`Not-Set`"),
            "Role": getattr(self.record.success_role, "mention", "`Not-Set`"),
            "Required SS": f"`{self.record.required_ss}`",
            "Screenshot Type": "`Not-Set`" if not self.record.screenshot_type else f"`{self.record.screenshot_type.value.title()}`",
            "Page / Channel Name": f"`{self.record.entity_name or '`Not-Set`'}`",
            "Page URL (Optional)": (
                "`Not-Set`"
                if not self.record.entity_link
                else f"[{self.record.entity_link.replace('https://','').replace('www.','')}]({self.record.entity_link})"
            ),
            "Allow Duplicates?": "`Yes`" if self.record.allow_duplicate_ss else "`No`",
        }

        for idx, (name, value) in enumerate(fields.items(), start=1):
            e.add_field(
                name=f"{keycap_digit(idx)} {name}:",
                value=value,
            )

        return e

    async def refresh_view(self):
        e = self.initial_msg()

        if all(
            (
                self.record.channel_id,
                self.record.role_id,
                self.record.required_ss,
                self.record.entity_name,
                self.record.screenshot_type,
            )
        ):
            self.children[-1].disabled = False

        try:
            self.message = await self.message.edit(embed=e, view=self)
        except discord.HTTPException:
            await self.on_timeout()
