from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord.ext import commands
from lib import INFO
from models import Scrim

from .events import ScrimsEvents
from .slash import ScrimSlashCommands
from .views.scrims.main_panel import ScrimsMainPanel


class Esports(commands.Cog):
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


async def setup(bot: Quotient) -> None:
    await bot.add_cog(Esports(bot))
    await bot.add_cog(ScrimSlashCommands(bot))
    await bot.add_cog(ScrimsEvents(bot))
