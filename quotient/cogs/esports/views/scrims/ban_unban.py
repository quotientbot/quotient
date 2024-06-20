import discord
from discord.ext import commands
from lib import EXIT, INFO
from models import Scrim

from . import ScrimsBtn, ScrimsView
from .utility.buttons import DiscardChanges
from .utility.common import get_scrim_position
from .utility.paginator import NextScrim, PreviousScrim, SkipToScrim


class ScrimBanManager(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx, timeout=100)

        self.record = scrim

    async def initial_msg(self) -> discord.Embed:
        banned_teams = await self.record.banned_teams.all()
        scrims = await Scrim.filter(guild_id=self.record.guild_id).order_by("reg_start_time")

        self.clear_items()

        self.add_item(BanUsers(self.ctx))
        self.add_item(UnbanUsers(self.ctx, disabled=not banned_teams))
        self.add_item(UnbanAllUsers(self.ctx, disabled=not banned_teams))
        self.add_item(BannedSlotInfo(self.ctx, disabled=not banned_teams))

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx, row=2))
            self.add_item(SkipToScrim(self.ctx, row=2))
            self.add_item(NextScrim(self.ctx, row=2))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT, row=2))

        embed = discord.Embed(color=self.bot.color)
        embed.description = f"**Ban / Unban users from {self.record}**\n\n"

        for idx, team in enumerate(banned_teams, start=1):
            embed.description += (
                f"`{idx:02}.` {getattr(team.leader,'mention','Unknown User')} - "
                f"{discord.utils.format_dt(team.banned_till,'R') if team.banned_till else '`Lifetime`'}\n"
            )

        if not banned_teams:
            embed.description += "```No teams are banned.```"

        embed.set_footer(text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.record.guild_id))}")
        return embed

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()


class BanUsers(ScrimsBtn):
    view: ScrimBanManager

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.red, label="Ban Users")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()


class UnbanUsers(ScrimsBtn):
    view: ScrimBanManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, disabled=disabled, style=discord.ButtonStyle.green, label="Unban Users")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()


class UnbanAllUsers(ScrimsBtn):
    view: ScrimBanManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, disabled=disabled, style=discord.ButtonStyle.green, label="Unban All Users")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()


class BannedSlotInfo(ScrimsBtn):
    view: ScrimBanManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, disabled=disabled, label="Info", emoji=INFO)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.view.refresh_view()
