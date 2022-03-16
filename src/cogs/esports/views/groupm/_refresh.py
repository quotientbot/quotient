from __future__ import annotations

import typing as T
from models import Tourney, TGroupList
import discord

__all__ = ("GroupRefresh",)


class GroupRefresh(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(custom_id="t_groups_refresh", label="Refresh", style=discord.ButtonStyle.green)
    async def refresh_group(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if not Tourney.is_ignorable(interaction.user) and not interaction.user.guild_permissions.manage_guild:
            return await interaction.followup.send(
                "You need either `manage-server` permissions or `@tourney-mod` role to refresh grouplist.", ephemeral=True
            )

        record = await TGroupList.get_or_none(pk=interaction.message.id, channel_id=interaction.channel_id)
        if not record:
            self.children[0].disabled = True
            return await interaction.edit_original_message(view=self)

        if (record.bot.current_time - record.refresh_at).total_seconds() < 120:
            return await interaction.followup.send("You can only refresh every 2 minutes.", ephemeral=True)

        await interaction.followup.send("Grouplist message was refreshed successfully.", ephemeral=True)
