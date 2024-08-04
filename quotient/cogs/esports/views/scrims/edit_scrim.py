import discord
from discord.ext import commands
from discord.utils import format_dt as fdt
from lib import DIAMOND, EXIT, F_WORD

from quotient.models import Scrim

from . import ScrimsView
from .utility.buttons import DiscardChanges
from .utility.callbacks import EDIT_OPTIONS
from .utility.common import get_scrim_position
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
                    emoji="🆓",
                )
                for option in EDIT_OPTIONS
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
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = scrim

    async def initial_msg(self):
        scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")
        self.clear_items()

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx))
            self.add_item(SkipToScrim(self.ctx))
            self.add_item(NextScrim(self.ctx))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT))

        self.add_item(ScrimsEditSelect(self.ctx, free_options_only=True))
        self.add_item(ScrimsEditSelect(self.ctx, free_options_only=False))

        embed = discord.Embed(
            title="Scrims Editor - Edit Settings",
            color=self.bot.color,
            url=self.bot.config("SUPPORT_SERVER_LINK"),
            description=f"**You are editing, {self.record}**",
        )

        s = self.record

        fields = {
            f"{F_WORD}Req. Mentions": f"`{s.required_mentions}`",
            f"{F_WORD}Total Slots": f"`{s.total_slots}`",
            f"{F_WORD}Reg Start Time": fdt(s.reg_start_time, "t") + " IST",
            f"{F_WORD}Match Start Time": fdt(s.match_start_time, "t") if s.match_start_time else "`Not Set`",
            f"{F_WORD}Reg Start Ping Role": getattr(s.start_ping_role, "mention", "`Not Set`"),
            f"{F_WORD}Reg Open Role": getattr(s.open_role, "mention", "`Not Set`"),
            f"{F_WORD}Multiple Reg": ("`Not Allowed`", "`Allowed`")[s.allow_multiple_registrations],
            f"{F_WORD}Reg Without Teamname": ("`Not Allowed`", "`Allowed`")[s.allow_without_teamname],
            f"{F_WORD}Reg Open Days": f"`{s.pretty_registration_days}`",
            f"{DIAMOND}Min Req Lines": ("`Not Set`", f"`{s.required_lines}`")[bool(s.required_lines)],
            f"{DIAMOND}Fake Mentions": ("`Not Allowed`", "`Allowed`")[s.allow_duplicate_mentions],
            f"{DIAMOND}Duplicate Teamname": ("`Not Allowed`", "`Allowed`")[s.allow_duplicate_teamname],
            f"{DIAMOND}Delete Extra Msgs": ("`No`", "`Yes`")[s.autodelete_extra_msges],
            f"{DIAMOND}Delete Rejected Regs": ("`No`", "`Yes`")[s.autodelete_rejected_registrations],
            f"{DIAMOND}Reg End Ping Role": getattr(s.end_ping_role, "mention", "`Not Set`"),
            f"{DIAMOND}Channel Autoclean time": (
                fdt(self.record.autoclean_channel_time, "t") + " IST" if s.autoclean_channel_time else "`Not Set`"
            ),
            f"{DIAMOND}Reg Auto-end time": fdt(s.reg_auto_end_time, "t") + " IST" if s.reg_auto_end_time else "`Not Set`",
            f"{DIAMOND}Share IDP with": f"`{s.idp_share_type.name.replace('_', ' ').title()}`",
            f"{DIAMOND}Slotlist Start From": f"`{s.slotlist_start_from}`",
            f"{DIAMOND}Auto-Send Slotlist": ("`No`", "`Yes`")[s.autosend_slotlist],
            f"{DIAMOND}Reactions": ", ".join(s.reactions),
        }

        for name, value in fields.items():
            embed.add_field(
                name=f"{name}:",
                value=value,
            )

        # embed.add_field(name="\u200b", value="\u200b")  # invisible field
        embed.set_footer(text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.ctx.guild.id))}")

        return embed

    async def refresh_view(self):
        await self.record.save()
        await self.record.refresh_timers()

        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()
