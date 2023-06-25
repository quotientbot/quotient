from __future__ import annotations

from string import ascii_uppercase
from typing import List

import discord

from core import Context
from models import Tourney
from utils import regional_indicator as ri

from ..paginator import NextButton, PrevButton, StopButton
from ._base import TourneyView
from ._buttons import (AutodeleteRejected, ConfirmChannel, DeleteTourney,
                       DiscardButton, DuplicateTags, DuplicateTeamName,
                       MinLines, MultiReg, OpenRole, RegChannel, SetEmojis,
                       SetGroupSize, SetMentions, SetPingRole, SetRole,
                       SetSlots, SetTourneyname, SuccessMessage,
                       TeamCompulsion)


class TourneyEditor(TourneyView):
    record: Tourney

    def __init__(self, ctx: Context, records):
        super().__init__(ctx, timeout=60, name="Tourney Editor")

        self.ctx = ctx

        self.records: List[Tourney] = records

        self.record = records[0]

        self.current_page = 1

    async def refresh_view(self):
        self.record = self.records[self.current_page - 1]

        _d = dict(self.record)

        del _d["id"]
        del _d["banned_users"]

        await Tourney.filter(pk=self.record.pk).update(**_d)

        _e = await self.initial_message()

        await self._add_buttons(self.ctx)

        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    async def initial_message(self):
        tourney = self.record
        _e = discord.Embed(color=self.ctx.bot.color, url=self.ctx.config.SERVER_LINK)
        _e.title = "Tournament Editor - Edit Settings"

        fields = {
            "Name": f"`{tourney.name}`",
            "Registration Channel": getattr(tourney.registration_channel, "mention", "`channel-deleted`"),
            "Confirm Channel": getattr(tourney.confirm_channel, "mention", "`channel-deleted`"),
            "Success Role": getattr(tourney.role, "mention", "`role-deleted`"),
            "Mentions": f"`{tourney.required_mentions}`",
            "Slots": f"`{tourney.total_slots:,}`",
            f"Reactions {self.bot.config.PRIME_EMOJI}": f"{tourney.check_emoji},{tourney.cross_emoji}",
            "Ping Role": getattr(tourney.ping_role, "mention", "`Not-Set`"),
            "Open Role": getattr(tourney.open_role, "mention", "`role-deleted`"),
            "Multi-Register": ("`Not allowed!`", "`Allowed`")[tourney.multiregister],
            "Team-Name Compulsion": ("`No!`", "`Yes!`")[tourney.teamname_compulsion],
            "Duplicate Team Name": ("`Allowed`", "`Not allowed!`")[tourney.no_duplicate_name],
            "Autodelete Rejected": ("`No!`", "`Yes!`")[tourney.autodelete_rejected],
            "Success Message": f"`Click to view / edit`",
            "Teams per Group": f"`{self.record.group_size or 'Not set'}`",
            f"Required Lines {self.bot.config.PRIME_EMOJI}": ("`Not set`", f"`{tourney.required_lines}`")[
                bool(tourney.required_lines)
            ],
            f"Duplicate / Fake Tags {self.bot.config.PRIME_EMOJI}": ("`Not allowed!`", "`Allowed`")[
                tourney.allow_duplicate_tags
            ],
        }

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )

        _e.add_field(name="\u200b", value="\u200b")
        _e.set_footer(text=f"Page {self.current_page}/{len(self.records)}")
        return _e

    async def _add_buttons(self, ctx: Context):
        self.clear_items()

        cur_page = self.current_page - 1

        if cur_page > 0:
            self.add_item(PrevButton())

        self.add_item(StopButton())

        if len(self.records) > 1 and cur_page < len(self.records) - 1:
            self.add_item(NextButton())

        self.add_item(SetTourneyname(ctx, "a"))
        self.add_item(RegChannel(ctx, "b"))
        self.add_item(ConfirmChannel(ctx, "c"))
        self.add_item(SetRole(ctx, "d"))
        self.add_item(SetMentions(ctx, "e"))
        self.add_item(SetSlots(ctx, "f"))
        self.add_item(SetEmojis(ctx, "g"))
        self.add_item(SetPingRole(ctx, "h"))
        self.add_item(OpenRole(ctx, "i"))
        self.add_item(MultiReg(ctx, "j"))
        self.add_item(TeamCompulsion(ctx, "k"))
        self.add_item(DuplicateTeamName(ctx, "l"))
        self.add_item(AutodeleteRejected(ctx, "m"))
        self.add_item(SuccessMessage(ctx, "n"))
        self.add_item(SetGroupSize(ctx, "o"))
        self.add_item(MinLines(ctx, "p"))
        self.add_item(DuplicateTags(ctx, "q"))
        self.add_item(DeleteTourney(ctx))
        self.add_item(DiscardButton(ctx))
