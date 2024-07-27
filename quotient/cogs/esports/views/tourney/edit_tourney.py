import discord
from cogs.esports.views.tourney import TourneyView
from discord.ext import commands
from discord.utils import format_dt as fdt
from lib import DIAMOND, EXIT, F_WORD, truncate_string
from models import Guild, Tourney

from .utility.buttons import DiscardChanges
from .utility.callbacks import EDIT_OPTIONS
from .utility.common import get_tourney_position
from .utility.paginator import NextTourney, PreviousTourney, SkipToTourney


class TourneysEditSelect(discord.ui.Select):
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


class TourneysEditPanel(TourneyView):
    def __init__(self, ctx: commands.Context, tourney: Tourney, guild: Guild):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = tourney
        self.guild = guild

    async def initial_msg(self):
        tourneys = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id")
        self.clear_items()

        if len(tourneys) > 1:
            self.add_item(PreviousTourney(self.ctx))
            self.add_item(SkipToTourney(self.ctx))
            self.add_item(NextTourney(self.ctx))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT))

        self.add_item(TourneysEditSelect(self.ctx, free_options_only=True))
        self.add_item(TourneysEditSelect(self.ctx, free_options_only=False, disabled=not self.guild.is_premium))

        embed = discord.Embed(
            title="Tourneys Editor - Edit Settings",
            color=self.bot.color,
            url=self.bot.config("SUPPORT_SERVER_LINK"),
            description=f"**You are editing, {self.record}**",
        )

        s = self.record

        fields = {
            f"{F_WORD}Name": f"`{s.name}`",
            f"{F_WORD}Confirmation Channel": getattr(s.confirm_channel, "mention", "`Not Set`"),
            f"{F_WORD}Success Role": getattr(s.success_role, "mention", "`Not Set`"),
            f"{F_WORD}Total Slots": f"`{s.total_slots:,}`",
            f"{F_WORD}Reg Start Ping Role": getattr(s.reg_start_ping_role, "mention", "`Not Set`"),
            f"{F_WORD}Allow Multiple Reg.": ["`No`", "`Yes`"][s.allow_multiple_registrations],
            f"{F_WORD}Allow without TeamName": ["`No`", "`Yes`"][s.allow_without_teamname],
            f"{F_WORD}Teams per Group": f"`{s.group_size}`",
            f"{DIAMOND}Success Message": (
                truncate_string(f"`{s.registration_success_dm_msg}`", 50, suffix="...`")
                if s.registration_success_dm_msg
                else "`Not Set`"
            ),
            f"{DIAMOND}Auto Del Rejected Reg": ["`No`", "`Yes`"][s.autodelete_rejected_registrations],
            f"{DIAMOND}Allow Duplicate TeamName": ["`No`", "`Yes`"][s.allow_duplicate_teamname],
            f"{DIAMOND}Reactions": f"{s.tick_emoji}, {s.cross_emoji}",
            f"{DIAMOND}Required Lines": f"`{s.required_lines}`" if s.required_lines else "`Not Set`",
            f"{DIAMOND}Allow Fake Tags": ["`No`", "`Yes`"][s.allow_duplicate_mentions],
        }

        for name, value in fields.items():
            embed.add_field(
                name=f"{name}:",
                value=value,
            )

        embed.add_field(name="\u200b", value="\u200b")  # invisible field
        embed.set_footer(text=f"Page - {' / '.join(await get_tourney_position(self.record.pk, self.ctx.guild.id))}")

        return embed

    async def refresh_view(self):
        await self.record.save()

        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()
