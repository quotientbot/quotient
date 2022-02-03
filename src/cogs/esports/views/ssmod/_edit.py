from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core import Quotient

from core import Context
from models import SSVerify

from ...views.base import EsportsBaseView
from ..paginator import NextButton, PrevButton

from ._buttons import *
import config


class SSmodEditor(EsportsBaseView):
    def __init__(self, ctx: Context, records: List[SSVerify]):
        super().__init__(ctx)

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

        self.records = records

        self.current_page = 0

    async def refresh_view(self):
        _e = await self.initial_embed(self.records[self.current_page])
        await self.__add_buttons(self.ctx)

        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    async def initial_embed(self, record: SSVerify):
        _index = self.records.index(record)
        await record.refresh_from_db()
        self.records[_index] = record

        _e = discord.Embed(color=0x00FFB3, title=f"Screenshots Manager - Edit Config", url=config.SERVER_LINK)

        fields = {
            "Channel": getattr(record.channel, "mention", "`deleted-channel`"),
            "Role": getattr(record.role, "mention", "`deleted-role`"),
            "Required ss": f"`{record.required_ss}`",
            "Screenshot Type": f"`{record.ss_type.value.title()}`",
            "Page Name": f"`{record.channel_name}`",
            "Page URL": f"[Click Here]({record.channel_link})",
            "Allow Same SS": "`Yes`" if record.allow_same else "`No`",
        }

        for _idx, (name, value) in enumerate(fields.items(), start=1):
            _e.add_field(
                name=f"{kd(_idx)} {name}:",
                value=value,
            )

        return _e

    async def __add_buttons(self, ctx):
        self.children.clear()

        if self.current_page > 0:
            self.add_item(PrevButton(self))

        if len(self.records) > 1 and self.current_page < len(self.records) - 1:
            self.add_item(NextButton(self))

        self.add_item(SetChannel(ctx))
        self.add_item(SetRole(ctx))
        self.add_item(RequiredSS(ctx))
        self.add_item(ScreenshotType(ctx))
        self.add_item(PageName(ctx))
        self.add_item(PageLink(ctx))
        self.add_item(AllowSame())
