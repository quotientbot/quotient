from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from cogs.esports.views.tourney.main_panel import TourneysMainPanel
from discord import app_commands
from discord.ext import commands
from lib import INFO
from models import Tourney


class TourneySlashCommands(commands.GroupCog, name="tourney"):
    def __init__(self, bot: Quotient):
        self.bot = bot

        super().__init__()

    def can_use_tourney_command():
        async def predicate(inter: discord.Interaction) -> bool:
            if not any((inter.user.guild_permissions.manage_guild, Tourney.is_ignorable(inter.user))):
                await inter.response.send_message(
                    embed=discord.Embed(
                        color=discord.Color.red(),
                        description=f"You need `tourney-mod` role or `Manage-Server` permissions to use this command.",
                    )
                )
                return False

            return True

        return app_commands.check(predicate)

    @app_commands.command(name="panel", description="Shows the main dashboard to manage tourneys.")
    @app_commands.guild_only()
    @can_use_tourney_command()
    async def tourney_panel(self, inter: discord.Interaction):
        await inter.response.defer(thinking=True)

        ctx = await self.bot.get_context(inter)
        v = TourneysMainPanel(ctx)
        v.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )
        v.message = await inter.followup.send(embed=await v.initial_msg(), view=v)
