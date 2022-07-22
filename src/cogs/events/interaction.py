from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Cog
from discord.app_commands import AppCommandError

__all__ = ("InteractionErrors",)


class InteractionErrors(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.tree.interaction_check = self.global_interaction_check
        self.bot.tree.on_error = self.on_app_command_error

    async def global_interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.guild_id:
            await interaction.response.send_message(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description="Application commands can not be used in Private Messages.",
                ),
                ephemeral=True,
            )

            return False

        return True

    async def on_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, discord.NotFound):
            return  # these unknown interactions are annoying :pain:

        # rest later
