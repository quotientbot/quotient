from __future__ import annotations

import typing as T
from string import ascii_uppercase

import discord

from core import Context
from models import Scrim, Timer
from utils import discord_timestamp as dt
from utils import regional_indicator as ri

from ._base import ScrimsView
from ._btns import *
from ._pages import *


class ScrimsEditor(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx, timeout=60.0)
        self.ctx = ctx
        self.record = scrim

        self.page_info = ("x", "y")

    async def refresh_view(self):
        _d = dict(self.record)

        del _d["id"]
        del _d["autoclean"]
        del _d["available_slots"]
        del _d["open_days"]

        await Timer.filter(extra={"args": [], "kwargs": {"scrim_id": self.record.id}}, event="scrim_open").delete()
        await self.bot.reminders.create_timer(_d["open_time"], "scrim_open", scrim_id=self.record.id)

        await self.bot.db.execute(
            """UPDATE public."sm.scrims" SET open_days = $1 WHERE id = $2""",
            [_.value for _ in self.record.open_days],
            self.record.id,
        )

        await self.record.make_changes(**_d)

        await self._add_buttons()
        try:
            self.message = await self.message.edit(embed=await self.initial_message, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @property
    async def initial_message(self):
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
            "Open Time": f"{dt(scrim.open_time,'t')} ({dt(scrim.open_time)})",
            f"Reactions {self.bot.config.PRIME_EMOJI}": f"{scrim.check_emoji},{scrim.cross_emoji}",
            "Ping Role": getattr(scrim.ping_role, "mention", "`Not-Set`"),
            "Open Role": getattr(scrim.open_role, "mention", "`role-deleted`"),
            "Multi-Register": ("`Not allowed!`", "`Allowed`")[scrim.multiregister],
            "Team Compulsion": ("`No!`", "`Yes!`")[scrim.teamname_compulsion],
            "Duplicate Team Name": ("`Allowed`", "`Not allowed!`")[scrim.no_duplicate_name],
            "Autodelete Rejected": ("`No!`", "`Yes!`")[scrim.autodelete_rejects],
            "Autodelete Late Messages": ("`No!`", "`Yes!`")[scrim.autodelete_extras],
            "Slotlist Start from": "`{}`".format(scrim.start_from),
            "Autoclean": f"{dt(scrim.autoclean_time,'t')} (`{', '.join(_.name.title() for _ in scrim.autoclean)}`)"
            if scrim.autoclean_time
            else "`Turned OFF`",
            "Scrim Days": ", ".join(map(lambda x: "`{0}`".format(x.name.title()[:2]), self.record.open_days))
            if self.record.open_days
            else "`Not set`",
            f"Required Lines {self.bot.config.PRIME_EMOJI}": ("`Not set`", "`{0}`".format(scrim.required_lines))[
                bool(scrim.required_lines)
            ],
            f"Duplicate / Fake Tags {self.bot.config.PRIME_EMOJI}": ("`Not allowed!`", "`Allowed`")[
                scrim.allow_duplicate_tags
            ],
        }

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )
        _e.add_field(name="\u200b", value="\u200b")  # invisible field
        _e.set_footer(text=f"Page - {' / '.join(await self.record.scrim_posi())}")
        return _e

    async def _add_buttons(self):
        self.clear_items()

        if await Scrim.filter(guild_id=self.ctx.guild.id).count() >= 2:
            self.add_item(Prev(self.ctx))
            self.add_item(SkipTo(self.ctx))
            self.add_item(Next(self.ctx))

        self.add_item(SetName(self.ctx, "a"))
        self.add_item(RegChannel(self.ctx, "b"))
        self.add_item(SlotChannel(self.ctx, "c"))
        self.add_item(SetRole(self.ctx, "d"))
        self.add_item(SetMentions(self.ctx, "e"))
        self.add_item(TotalSlots(self.ctx, "f"))
        self.add_item(OpenTime(self.ctx, "g"))
        self.add_item(SetEmojis(self.ctx, "h"))
        self.add_item(PingRole(self.ctx, "i"))
        self.add_item(OpenRole(self.ctx, "j"))

        self.add_item(MultiReg(self.ctx, "k"))
        self.add_item(TeamCompulsion(self.ctx, "l"))
        self.add_item(DuplicateTeam(self.ctx, "m"))
        self.add_item(DeleteReject(self.ctx, "n"))
        self.add_item(DeleteLate(self.ctx, "o"))
        self.add_item(SlotlistStart(self.ctx, "p"))
        self.add_item(SetAutoclean(self.ctx, "q"))
        self.add_item(OpenDays(self.ctx, "r"))
        self.add_item(MinLines(self.ctx, "s"))
        self.add_item(DuplicateTags(self.ctx, "t"))

        self.add_item(DeleteScrim(self.ctx))
        self.add_item(Discard(self.ctx, "Main Menu"))
