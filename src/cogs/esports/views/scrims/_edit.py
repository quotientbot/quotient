from __future__ import annotations

import typing as T
from string import ascii_uppercase

import discord

from core import Context
from models import Scrim
from utils import regional_indicator as ri

from ._base import ScrimsView


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

        fields = {
            "Name": "`{0}`".format(scrim.name),
            "Registration Channel": getattr(scrim.registration_channel, "mention", "`channel-deleted`"),
            "Slotlist Channel": getattr(scrim.slotlist_channel, "mention", "`deleted-channel`"),
            "Success Role": getattr(scrim.role, "mention", "`role-deleted`"),
            "Mentions": f"`{scrim.required_mentions}`",
            "Slots": f"`{scrim.total_slots}`",
            "Open Time": scrim.open_time.strftime("%I:%M %p"),
            f"Reactions {self.bot.config.PRIME_EMOJI}": f"{scrim.check_emoji},{scrim.cross_emoji}",
            "Autoclean": f"{scrim.autoclean_time.strftime('%I:%M %p')} [{', '.join(scrim.autoclean)}]"
            if scrim.autoclean
            else "`Turned OFF`",
            "Ping Role": getattr(scrim.ping_role, "mention", "`Not-Set`"),
            "Open Role": getattr(scrim.open_role, "mention", "`role-deleted`"),
            "Multi-Register": ("`Not allowed!`", "`Allowed`")[scrim.multiregister],
            "Team Compulsion": ("`No!`", "`Yes!`")[scrim.teamname_compulsion],
            "Duplicate Team Name": ("`Allowed`", "`Not allowed!`")[scrim.no_duplicate_name],
            "Autodelete Rejected": ("`No!`", "`Yes!`")[scrim.autodelete_rejects],
            "Autodelete Late Messages": ("`No!`", "`Yes!`")[scrim.autodelete_extras],
            "Slotlist Start from": scrim.start_from,
        }

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )
        _e.set_footer(text=f"Page {self.current_page}/{len(self.records)}", icon_url=self.ctx.bot.user.avatar.url)
        return _e

    async def _add_buttons(self):
        self.clear_items()
