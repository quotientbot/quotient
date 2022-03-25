from __future__ import annotations
import typing as T

from ._base import ScrimsView
from core import Context
from models import Scrim
import discord

from string import ascii_uppercase
from utils import regional_indicator as ri


class ScrimsEditor(ScrimsView):
    def __init__(self, ctx: Context, records):
        super().__init__(ctx, timeout=60.0)
        self.ctx = ctx

        self.records: T.List[Scrim] = records
        self.record = self.records[0]
        self.current_page = 1

    async def refresh_view(self):
        ...

    @property
    def initial_message(self):
        scrim = self.record

        _e = discord.Embed(color=0x00FFB3, url=self.ctx.config.SERVER_LINK)
        _e.title = "Scrims Editor - Edit Settings"

        fields = {}

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )
        _e.set_footer(text=f"Page {self.current_page}/{len(self.records)}", icon_url=self.ctx.bot.user.avatar.url)
        return _e

        return _e
