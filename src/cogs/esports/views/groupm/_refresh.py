from __future__ import annotations

import typing as T
from models import Tourney, TGroupList
import discord

__all__ = ("GroupRefresh",)


class GroupRefresh(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        custom_id="t_groups_refresh",
        emoji="<:refresh:953888517619064833>",
        label="Refresh",
        style=discord.ButtonStyle.green,
    )
    async def refresh_group(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if not Tourney.is_ignorable(interaction.user) and not interaction.user.guild_permissions.manage_guild:
            return await interaction.followup.send(
                "You need either `manage-server` permissions or `@tourney-mod` role to refresh grouplist.", ephemeral=True
            )

        record = await TGroupList.get_or_none(pk=interaction.message.id)
        tourney = None
        if record:
            tourney = await Tourney.get_or_none(pk=record.tourney_id)

        if not record or not tourney:
            self.children[0].disabled = True
            return await interaction.edit_original_message(view=self)

        if (record.bot.current_time - record.refresh_at).total_seconds() < 120:
            return await interaction.followup.send("You can only refresh every 2 minutes.", ephemeral=True)

        group = await tourney.get_group(record.group_number)
        if not group:
            await interaction.delete_original_message()
            return await interaction.followup.send("Group not found.", ephemeral=True)

        await TGroupList.filter(pk=record.pk).update(refresh_at=record.bot.current_time)

        _e = discord.Embed(color=0x00FFB3, title=f"{tourney.name} - Group {record.group_number}")
        _e.set_thumbnail(url=getattr(tourney.guild.icon, "url", discord.Embed.Empty))

        _e.description = (
            "```\n"
            + "".join(
                [f"Slot {idx:02}  ->  {slot.team_name}\n" for idx, slot in enumerate(group, tourney.slotlist_start)]
            )
            + "```"
        )
        _e.set_footer(text=tourney.guild.name, icon_url=getattr(tourney.guild.icon, "url", discord.Embed.Empty))

        await interaction.edit_original_message(embed=_e, view=self)
        await interaction.followup.send("Grouplist message was refreshed successfully.", ephemeral=True)
