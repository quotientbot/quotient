from string import ascii_uppercase

import discord
from discord.ext import commands

from quotient.lib import regional_indicator
from quotient.models import SSverify

from . import SsVerifyView
from .utility.buttons import (
    DeleteSsVerifySetup,
    DiscardButton,
    NextPage,
    PreviousPage,
    SetAllowDuplicateSS,
    SetEntityLink,
    SetEntityName,
    SetRegChannel,
    SetRequiredSS,
    SetScreenshotType,
    SetSuccessMessage,
    SetSuccessRole,
    SkipToPage,
)
from .utility.common import get_ssverify_position


class EditSsVerifySettings(SsVerifyView):
    def __init__(self, ctx: commands.Context, record: SSverify):
        super().__init__(ctx, timeout=100)
        self.record = record

    async def initial_msg(self) -> discord.Embed:
        self.clear_items()

        if await SSverify.filter(guild_id=self.ctx.guild.id).order_by("id").count() > 1:
            self.add_item(PreviousPage(self.ctx))
            self.add_item(SkipToPage(self.ctx))
            self.add_item(NextPage(self.ctx))

        self.add_item(SetRegChannel(self.ctx, regional_indicator("A")))
        self.add_item(SetSuccessRole(self.ctx, regional_indicator("B")))
        self.add_item(SetRequiredSS(self.ctx, regional_indicator("C")))
        self.add_item(SetScreenshotType(self.ctx, regional_indicator("D")))
        self.add_item(SetEntityName(self.ctx, regional_indicator("E")))
        self.add_item(SetEntityLink(self.ctx, regional_indicator("F")))
        self.add_item(SetAllowDuplicateSS(self.ctx, regional_indicator("G")))

        self.add_item(SetSuccessMessage(self.ctx, regional_indicator("H")))
        self.add_item(DeleteSsVerifySetup(self.ctx, self.record))
        self.add_item(DiscardButton(self.ctx, label="Back to Main Menu", style=discord.ButtonStyle.blurple))

        e = discord.Embed(color=self.bot.color, description=f"## Editing SSverify settings: {self.record}")

        fields = {
            "Channel": getattr(self.record.channel, "mention", "`deleted-channel`"),
            "Role": getattr(self.record.success_role, "mention", "`deleted-role`"),
            "Required ss": f"`{self.record.required_ss}`",
            "Screenshot Type": f"`{self.record.screenshot_type.value.title()}`",
            "Page / Channel Name": f"`{self.record.entity_name or '`Not-Set`'}`",
            "Page URL (Optional)": (
                "`Not-Set`"
                if not self.record.entity_link
                else f"[{self.record.entity_link.replace('https://','').replace('www.','')}]({self.record.entity_link})"
            ),
            "Allow Same SS": "`Yes`" if self.record.allow_duplicate_ss else "`No`",
            f"Success Message": "`Click to view or edit`",
        }

        for _idx, (name, value) in enumerate(fields.items()):
            e.add_field(
                name=f"{regional_indicator(ascii_uppercase[_idx])} {name}:",
                value=value,
            )
        e.add_field(name="\u200b", value="\u200b")
        e.set_footer(text=f"Page - {' / '.join(await get_ssverify_position(self.record.pk, self.ctx.guild.id))}")

        return e

    async def refresh_view(self):
        await self.record.save()

        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()
