from __future__ import annotations

from ...views.base import EsportsBaseView
from core import Context

from models import SSVerify

from utils import keycap_digit as kd
import discord

import config

from ._buttons import *

__all__ = ("SetupWizard",)


class SetupWizard(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx)

        self.ctx = ctx
        self.record = None

        self.add_item(SetChannel(ctx))
        self.add_item(SetRole(ctx))
        self.add_item(RequiredSS(ctx))
        self.add_item(ScreenshotType(ctx))
        self.add_item(PageName(ctx))
        self.add_item(PageLink(ctx))
        self.add_item(AllowSame())
        self.add_item(DiscardButton())
        self.add_item(SaveButton(ctx))

    def initial_message(self):
        if not self.record:
            self.record = SSVerify(guild_id=self.ctx.guild.id)

        _e = discord.Embed(color=0x00FFB3, title="Enter details & Press Save", url=config.SERVER_LINK)

        fields = {
            "Channel": getattr(self.record.channel, "mention", "`Not-Set`"),
            "Role": getattr(self.record.role, "mention", "`Not-Set`"),
            "Required ss": f"`{self.record.required_ss}`",
            "Screenshot Type": "`Not-Set`" if not self.record.ss_type else f"`{self.record.ss_type.value.title()}`",
            "Page Name": f"`{self.record.channel_name or '`Not-Set`'}`",
            "Page URL": "`Not-Set (Not Required)`"
            if self.record.channel_link == config.SERVER_LINK
            else f"[Click Here]({self.record.channel_link})",
            "Allow Same SS": "`Yes`" if self.record.allow_same else "`No`",
        }

        for _idx, (name, value) in enumerate(fields.items(), start=1):
            _e.add_field(
                name=f"{kd(_idx)} {name}:",
                value=value,
            )

        return _e

    async def refresh_view(self):
        _e = self.initial_message()

        if all(
            (
                self.record.channel_id,
                self.record.role_id,
                self.record.required_ss,
                self.record.ss_type,
                self.record.channel_name,
            )
        ):
            self.children[-1].disabled = False

        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()
