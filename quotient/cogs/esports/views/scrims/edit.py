import typing as T

import discord
from discord.ext import commands
from discord.utils import format_dt as fdt
from lib import DIAMOND
from models import Guild, Scrim

from ..scrims import ScrimsView


class EditOption(T.NamedTuple):
    label: str
    description: str
    premium_only: bool


EDIT_OPTIONS = [
    EditOption(label="Required Mentions", description="Set the number of mentions required to register", premium_only=False),
    EditOption(label="Total Slots", description="Set the total slots for the scrim", premium_only=False),
    EditOption(label="Registration Start Time", description="Set the registration start time", premium_only=False),
    EditOption(label="Match Start Time", description="Set the match start time (Actual Game of BGMI, FF, etc)", premium_only=False),
    EditOption(label="Registration Start Ping Role", description="Set the role to ping when registration starts", premium_only=False),
    EditOption(label="Registration Open Role", description="Set the role to ping when registration opens", premium_only=False),
    EditOption(label="Allow Multiple Registrations", description="Allow users to register multiple times", premium_only=False),
    EditOption(label="Allow Without Teamname", description="Allow users to register without a teamname", premium_only=False),
    EditOption(label="Registration Open Days", description="Set the days when registration is open", premium_only=False),
    EditOption(label="Required Lines", description="Set the number of lines required in registration", premium_only=True),
    EditOption(label="Allow Duplicate Mentions", description="Allow duplicate mentions in registration", premium_only=True),
    EditOption(label="Allow Duplicate Teamname", description="Allow duplicate teamnames in registration", premium_only=True),
    EditOption(label="Auto-Delete Extra Messages", description="Auto-delete extra messages in registration", premium_only=True),
    EditOption(label="Auto-Delete Rejected Registrations", description="Auto-delete rejected registrations", premium_only=True),
    EditOption(label="Registration End Ping Role", description="Set the role to ping when registration ends", premium_only=True),
    EditOption(label="Channel Autoclean Time", description="Set the time to autoclean the channel", premium_only=True),
    EditOption(label="Registration Auto-End Time", description="Set the time to auto-end registration", premium_only=True),
    EditOption(label="Share IDP With", description="Set the type of IDP sharing", premium_only=True),
    EditOption(label="Slotlist Start From", description="Set the first slot number of slotlist", premium_only=True),
    EditOption(label="Auto-Send Slotlist", description="Auto send the slotlist after reg ends.", premium_only=True),
]


class ScrimsEditSelect(discord.ui.Select):
    def __init__(self, scrim: Scrim, free_options_only: bool = True, disabled: bool = False):

        options = []
        if free_options_only:
            options = [
                discord.SelectOption(
                    label=option.label,
                    description=option.description,
                    emoji="🆓",
                )
                for option in EDIT_OPTIONS
                if not option.premium_only
            ]
        else:
            options = [
                discord.SelectOption(
                    label=option.label,
                    description=option.description,
                    emoji=DIAMOND,
                )
                for option in EDIT_OPTIONS
                if option.premium_only
            ]

        super().__init__(
            placeholder="Please Select an option to edit" + ("(Premium Only)" if not free_options_only else ""),
            options=options,
            disabled=disabled,
        )
        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class ScrimsEditPanel(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim, guild: Guild):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = scrim

        self.add_item(ScrimsEditSelect(scrim=scrim, free_options_only=True))
        self.add_item(ScrimsEditSelect(scrim=scrim, free_options_only=False, disabled=not guild.is_premium))

    async def initial_msg(self):
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
            f"Required Lines {DIAMOND}": ("`Not Set`", f"`{s.required_lines}`")[bool(s.required_lines)],
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
        }

        for idx, (name, value) in enumerate(fields.items(), start=1):
            embed.add_field(
                name=f"{name}:",
                value=value,
            )

        embed.add_field(name="\u200b", value="\u200b")  # invisible field
        # embed.set_footer(text=f"Page - {' / '.join(await self.record.scrim_posi())}")

        return embed
