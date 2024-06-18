from string import ascii_uppercase

import discord
from discord.ext import commands
from discord.utils import format_dt as fdt
from lib import DIAMOND, INFO
from lib import regional_indicator as ri
from models import Guild, Scrim

from . import ScrimsView
from .utility.buttons import DiscardChanges
from .utility.callbacks import EDIT_OPTIONS
from .utility.paginator import NextScrim, PreviousScrim, SkipToScrim


class ScrimsEditSelect(discord.ui.Select):
    def __init__(self, ctx: commands.Context, free_options_only: bool = True, disabled: bool = False):
        self.ctx = ctx

        options = []
        if free_options_only:
            options = [
                discord.SelectOption(
                    label=f"{option.label}",
                    description=option.description,
                    emoji=ri(ascii_uppercase[idx]),
                )
                for idx, option in enumerate(EDIT_OPTIONS)
                if not option.premium_guild_only
            ]
        else:
            options = [
                discord.SelectOption(
                    label=f"{option.label}",
                    description=option.description,
                    emoji=DIAMOND,
                )
                for option in EDIT_OPTIONS
                if option.premium_guild_only
            ]

        super().__init__(
            placeholder="Please Select an option to edit" + (" (Premium Only)" if not free_options_only else ""),
            options=options,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        handler = next(option.handler for option in EDIT_OPTIONS if option.label == self.values[0])
        await handler(self, interaction)


class ScrimsEditPanel(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim, guild: Guild):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = scrim
        self.guild = guild

    async def initial_msg(self):
        scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")
        scrim_position = [scrim.pk for scrim in scrims].index(self.record.pk) + 1

        self.clear_items()

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx))
            self.add_item(SkipToScrim(self.ctx))
            self.add_item(NextScrim(self.ctx))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji="<:exit:926048897548300339>"))

        self.add_item(ScrimsEditSelect(self.ctx, free_options_only=True))
        self.add_item(ScrimsEditSelect(self.ctx, free_options_only=False, disabled=not self.guild.is_premium))

        embed = discord.Embed(
            title="Scrims Editor - Edit Settings",
            color=self.bot.color,
            url=self.bot.config("SUPPORT_SERVER_LINK"),
        )

        s = self.record

        fields = {
            "Req. Mentions": f"`{s.required_mentions}`",
            "Total Slots": f"`{s.total_slots}`",
            "Reg Start Time": fdt(s.reg_start_time, "t"),
            "Match Start Time": fdt(s.match_start_time, "t") if s.match_start_time else "`Not Set`",
            "Reg Start Ping Role": getattr(s.start_ping_role, "mention", "`Not Set`"),
            "Reg Open Role": getattr(s.open_role, "mention", "`Not Set`"),
            "Multiple Reg": ("`Not Allowed`", "`Allowed`")[s.allow_multiple_registrations],
            "Reg Without Teamname": ("`Not Allowed`", "`Allowed`")[s.allow_without_teamname],
            "Reg Open Days": f"`{s.pretty_registration_days}`",
            f"Min Req Lines {DIAMOND}": ("`Not Set`", f"`{s.required_lines}`")[bool(s.required_lines)],
            f"Fake Mentions {DIAMOND}": ("`Not Allowed`", "`Allowed`")[s.allow_duplicate_mentions],
            f"Duplicate Teamname {DIAMOND}": ("`Not Allowed`", "`Allowed`")[s.allow_duplicate_teamname],
            f"Delete Extra Msgs {DIAMOND}": ("`No`", "`Yes`")[s.autodelete_extra_msges],
            f"Delete Rejected Regs {DIAMOND}": ("`No`", "`Yes`")[s.autodelete_rejected_registrations],
            f"Reg End Ping Role {DIAMOND}": getattr(s.end_ping_role, "mention", "`Not Set`"),
            f"Channel Autoclean time {DIAMOND}": fdt(self.record.autoclean_channel_time, "t"),
            f"Reg Auto-end time {DIAMOND}": fdt(s.reg_auto_end_time, "t") if s.reg_auto_end_time else "`Not Set`",
            f"Share IDP with {DIAMOND}": f"`{s.idp_share_type.name.replace('_', ' ').title()}`",
            f"Slotlist Start From {DIAMOND}": f"`{s.slotlist_start_from}`",
            f"Auto-Send Slotlist {DIAMOND}": ("`No`", "`Yes`")[s.autosend_slotlist],
            f"Reactions {DIAMOND}": ", ".join(s.reactions),
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )

        # embed.add_field(name="\u200b", value="\u200b")  # invisible field
        embed.set_footer(text=f"Page - {scrim_position} / {len(scrims)}")

        return embed

    async def refresh_view(self):
        await self.record.save()
        # TODO: add new timers for changed times.

        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()
