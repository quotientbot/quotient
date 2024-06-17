from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from core import Quotient

import discord
from core import QuoView
from discord.ext import commands
from models import Scrim


class EditOption(t.NamedTuple):
    label: str
    description: str


EDIT_OPTIONS = [
    EditOption(label="Name", description="The name of the scrim."),
    EditOption(label="Registration channel", description="The channel where registration happens."),
    EditOption(label="Slotlist channel", description="The channel where slotlist will be sent."),
    EditOption(label="Start Slotlist From", description="First slot number to start from."),
    EditOption(label="Auto-Send slotlist", description="Whether to send slotlist automatically after reg."),
    EditOption(label="Required Mentions", description="Number of mentions required in registration."),
    EditOption(label="Total Slots", description="Total number of slots in the scrim."),
    EditOption(label="Reg Start Time", description="Time when the scrim starts."),
    EditOption(label="Match Start Time", description="Time when the actual game will start."),
    EditOption(label="Success Role", description="Role to give to successful registrations."),
    EditOption(label="Reg Start Ping Role", description="Role to ping at reg start."),
    EditOption(label="Reg End Ping Role", description="Role to ping at reg end."),
    EditOption(label="Open Role", description="Role for which registration channel is opened."),
    EditOption(label="Allow Multiple Registrations", description="Whether same user can register multiple times."),
    EditOption(label="Autodelete Rejected Registrations", description="Whether to delete rejected registrations."),
    EditOption(label="Autodelete Extra Messages", description="Whether to delete extra messages after reg ends."),
    EditOption(label="Allow Without Teamname", description="Whether to allow registration without team name."),
    EditOption(label="Allow Duplicate Teamname", description="Whether same team name can be used multiple times."),
    EditOption(label="Allow Duplicate Mentions", description="Whether same user can be mentioned in multiple regs."),
    EditOption(label="Registration Open Days", description="Days when registration should be opened"),
    EditOption(label="Required Lines", description="Number of lines required for registration."),
]


class ScrimsEditSelect(discord.ui.Select):
    def __init__(self, scrim: Scrim):
        super().__init__(
            placeholder="Select an option to edit",
            options=[discord.SelectOption(label=option.label, description=option.description) for option in EDIT_OPTIONS],
        )
        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class ScrimsEditPanel(QuoView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = scrim

        self.add_item(ScrimsEditSelect(scrim=scrim))

    @property
    def initital_embed(self):
        embed = discord.Embed(
            title=f"Edit {self.record.name}",
            description="Select the option you want to edit.",
            color=self.bot.color,
        )
        return embed
