from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord.ext import commands
from lib import INFO

from quotient.models import Scrim, TagCheck

from .events import ScrimsEvents, TagCheckEvents
from .slash import ScrimSlashCommands, TourneySlashCommands
from .views.scrims.main_panel import ScrimsMainPanel
from .views.ssverify.main_panel import SsVerifyMainPanel
from .views.tagcheck.panel import TagCheckPanel


class Esports(commands.Cog):
    SUBCOGS = ("scrims", "tourney")

    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

    @commands.command(name="scrims", aliases=("sm", "s"))
    async def smanager(self, ctx: Context) -> None:
        """
        Manage scrims of the server.
        """
        if not any((ctx.author.guild_permissions.manage_guild, Scrim.is_ignorable(ctx.author))):
            return await ctx.send(
                embed=self.bot.error_embed("You need `scrims-mod` role or `Manage-Server` permissions to use this command.")
            )

        view = ScrimsMainPanel(ctx)
        view.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )

        view.message = await ctx.send(embed=await view.initial_msg(), view=view)

    @commands.hybrid_command(name="tagcheck", aliases=("tc",))
    async def tagcheck(self, ctx: Context) -> None:
        """
        Manage tag check settings of the server.
        """
        if not any((ctx.author.guild_permissions.manage_guild, TagCheck.ignorerole_role in ctx.author.roles)):
            return await ctx.send(
                embed=self.bot.error_embed("You need `quotient-tag-ignore` role or `Manage-Server` permissions to use this command.")
            )

        v = TagCheckPanel(ctx)
        v.message = await ctx.send(embed=await v.initial_msg(), view=v)

    @commands.hybrid_command(name="ssverify", aliases=("ss",))
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def ssverify_panel(self, ctx: Context) -> None:
        """
        Setup Screenshots Verification in the server.
        """
        await ctx.defer()

        v = SsVerifyMainPanel(ctx)
        v.message = await ctx.send(embed=await v.initial_msg(), view=v)


async def setup(bot: Quotient) -> None:
    await bot.add_cog(Esports(bot))
    await bot.add_cog(ScrimSlashCommands(bot))
    await bot.add_cog(TourneySlashCommands(bot))
    await bot.add_cog(ScrimsEvents(bot))
    await bot.add_cog(TagCheckEvents(bot))
