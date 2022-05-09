from __future__ import annotations

import typing as T

import discord

from models import TGroupList, TMSlot, Tourney
from utils import emote

from ..tourney._select import TourneySlotSelec

__all__ = ("GroupRefresh",)


class GroupRefresh(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not Tourney.is_ignorable(interaction.user) and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You need either `manage-server` permissions or `@tourney-mod` role to refresh grouplist.", ephemeral=True
            )
            return False

        return True

    @discord.ui.button(
        custom_id="t_groups_refresh",
        emoji="<:refresh:953888517619064833>",
        label="Refresh",
        style=discord.ButtonStyle.green,
    )
    async def refresh_group(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        _checks = await self.__do_checks(interaction, True)

        try:
            record, tourney, group = _checks
        except:
            return

        await TGroupList.filter(pk=record.pk).update(refresh_at=record.bot.current_time)

        _e = discord.Embed(color=0x00FFB3, title=f"{tourney.name} - Group {record.group_number}")
        # _e.set_thumbnail(url=getattr(tourney.guild.icon, "url", discord.Embed.Empty))

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

    @discord.ui.button(custom_id="gl_info_b", emoji=emote.info, label="Info")
    async def slots_info(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        _checks = await self.__do_checks(interaction)
        if not len(_checks) == 3:
            return

        record, tourney, group = _checks

        for _ in group:
            setattr(_, "tourney", tourney)

        v = discord.ui.View()
        v.add_item(TourneySlotSelec(group, "Select the slot to see the team info."))

        await interaction.followup.send("", view=v, ephemeral=True)
        await v.wait()
        if hasattr(v, "custom_id"):
            for _ in v.custom_id:
                slot_id, tourney_id = _.split(":")
                _slot = await TMSlot.get(pk=slot_id)

                member = await tourney.bot.get_or_fetch_member(tourney.guild, _slot.leader_id)
                _e = discord.Embed(color=0x00FFB3, title=f"Slot {group.index(_slot)+1}, Group {record.group_number}")
                _e.description = (
                    f"> Team Name: `{_slot.team_name}`\n"
                    f"> Team Leader: `{member}`\n"
                    f"> Registration Message: [Click here]({_slot.jump_url})\n"
                    f"> Confirm Message: [Click here]({_slot.confirm_jump_url})"
                )

                await interaction.followup.send(embed=_e, ephemeral=True)

    async def __do_checks(self, interaction: discord.Interaction, refresh_too=False):

        record = await TGroupList.get_or_none(pk=interaction.message.id)
        tourney = None
        if record:
            tourney = await Tourney.get_or_none(pk=record.tourney_id)

        if not record or not tourney:
            self.children[0].disabled = True
            return await interaction.edit_original_message(view=self)

        if refresh_too:
            if (record.bot.current_time - record.refresh_at).total_seconds() < 120:
                return await interaction.followup.send("You can only refresh every 2 minutes.", ephemeral=True)

        group = await tourney.get_group(record.group_number)
        if not group:
            await interaction.delete_original_message()
            return await interaction.followup.send("Group not found.", ephemeral=True)

        return record, tourney, group
