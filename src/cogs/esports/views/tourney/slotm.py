from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, List

from models import TMSlot, Tourney
from utils import BaseSelector, Prompt, emote, truncate_string

if TYPE_CHECKING:
    from core import Quotient

import asyncio

import discord
from tortoise.query_utils import Q

import config

from ...helpers import update_confirmed_message


class TCancelSlotSelector(discord.ui.Select):
    def __init__(self, bot: Quotient, slots: List[TMSlot], placeholder: str = "Select a slot to cancel"):

        _options = []
        for slot in slots:
            slot.members.append(slot.leader_id)

            description = f"Team: {', '.join((str(m) for m in map(bot.get_user, set(slot.members))))}"
            _options.append(
                discord.SelectOption(
                    label=f"Number {slot.num} ─ {slot.team_name.title()}",
                    description=truncate_string(description, 100),
                    value=slot.id,
                    emoji="<:text:815827264679706624>",
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class TourneySlotManager(discord.ui.View):
    def __init__(self, bot: Quotient, *, tourney: Tourney):

        self.tourney = tourney
        self.bot = bot
        self.title = "Tourney Slot Manager"
        super().__init__(timeout=None)

    def red_embed(self, description: str) -> discord.Embed:
        return discord.Embed(color=discord.Color.red(), title=self.title, description=description)

    async def update_channel_for(self, channel: discord.TextChannel, user, allow=True):
        if allow:
            return await channel.set_permissions(user, send_messages=True)

        return await channel.set_permissions(user, overwrite=None)

    @staticmethod
    def initial_embed(tourney: Tourney) -> discord.Embed:
        embed = discord.Embed(
            color=config.COLOR,
            description=(
                f"**[Tourney Slot Manager]({config.SERVER_LINK})** ─ {tourney}\n\n"
                "• Click `Cancel My Slot` below to cancel your slot.\n"
                "• Click `My Slots` to get info about all your slots.\n"
                "• Click `Change Team Name` if you want to update your team's name.\n\n"
                "*Note that slot cancel is irreversible.*"
            ),
        )
        return embed

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="tourney-cancel-slot", label="Cancel My Slot")
    async def cancel_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        _slots = await self.tourney.assigned_slots.filter(
            Q(leader_id=interaction.user.id) | Q(members__contains=interaction.user.id)
        ).order_by("num")

        if not _slots:
            return await interaction.followup.send(
                embed=self.red_embed(f"You don't have any slot, because you haven't registered in {self.tourney} yet."),
                ephemeral=True,
            )

        cancel_view = BaseSelector(interaction.user.id, TCancelSlotSelector, bot=self.bot, slots=_slots)
        await interaction.followup.send("Kindly choose one of the following slots", view=cancel_view, ephemeral=True)

        await cancel_view.wait()

        if _id := cancel_view.custom_id:

            prompt = Prompt(interaction.user.id)
            await interaction.followup.send("Are you sure you want to cancel your slot?", view=prompt, ephemeral=True)
            await prompt.wait()

            if not prompt.value:
                return await interaction.followup.send("Alright, Aborting.", ephemeral=True)

            slot = await TMSlot.get_or_none(pk=_id)
            if not slot:
                return await interaction.followup.send(embed=self.red_embed("Slot is already deleted."), ephemeral=True)

            if slot.confirm_jump_url:
                self.bot.loop.create_task(update_confirmed_message(self.tourney, slot.confirm_jump_url))

            if len(_slots) == 1:
                member = interaction.guild.get_member(slot.leader_id)
                if member:
                    self.bot.loop.create_task(member.remove_roles(self.tourney.role))

            await TMSlot.filter(pk=slot.id).delete()
            return await interaction.followup.send(f"{emote.check} | Your slot was removed.", ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="tourney-slot-info", label="My Groups")
    async def _slots_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        _slots = await self.tourney.assigned_slots.filter(
            Q(leader_id=interaction.user.id) | Q(members__contains=interaction.user.id)
        ).order_by("num")

        if not _slots:
            return await interaction.followup.send(
                embed=self.red_embed(f"You don't have any slot, because you haven't registered in {self.tourney} yet."),
                ephemeral=True,
            )

        embed = discord.Embed(color=config.COLOR)
        embed.description = f"Your have the following slots in {self.tourney}:\n\n"

        for idx, slot in enumerate(_slots, start=1):
            embed.description += (
                f"`{idx}.` **{slot.team_name.title()}** (**[Slot {slot.num}]({slot.confirm_jump_url})**)\n"
            )

        return await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="tourney-slot_name", label="Change Team Name")
    async def _change_slot_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        _slots = await self.tourney.assigned_slots.filter(
            Q(leader_id=interaction.user.id) | Q(members__contains=interaction.user.id)
        ).order_by("num")

        if not _slots:
            return await interaction.followup.send(
                embed=self.red_embed(f"You don't have any slot, because you haven't registered in {self.tourney} yet."),
                ephemeral=True,
            )

        cancel_view = BaseSelector(
            interaction.user.id,
            TCancelSlotSelector,
            bot=self.bot,
            slots=_slots,
            placeholder="Select a slot to change Name",
        )
        await interaction.followup.send("Kindly choose one of the following slots", view=cancel_view, ephemeral=True)

        await cancel_view.wait()

        if _id := cancel_view.custom_id:
            await interaction.followup.send("Enter the new name for your team.", ephemeral=True)

            await self.update_channel_for(interaction.channel, interaction.user)

            try:
                team_name: discord.Message = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id,
                    timeout=30,
                )
            except asyncio.TimeoutError:
                await self.update_channel_for(interaction.channel, interaction.user, False)
                return await interaction.followup.send("Timed out. Please try again later.", ephemeral=True)

            with suppress(discord.HTTPException):
                await self.update_channel_for(interaction.channel, interaction.user, False)

                await team_name.delete()

                await TMSlot.filter(pk=_id).update(team_name=truncate_string(team_name.content, 30))
                return await interaction.followup.send(f"{emote.check} | Your team name was changed.", ephemeral=True)

    @discord.ui.button(emoji="<:swap:954022423542509598>", label="Swap Groups", custom_id="tourney-swap-groups")
    async def tourney_group_swap(self, inter: discord.Interaction,button: discord.Button):
        await inter.response.defer()

        if not inter.user.guild_permissions.manage_guild and not Tourney.is_ignorable(inter.user):
            return await inter.followup.send(
                "You need either `@tourney-mod` role or `manage-server` permissions to swap groups.", ephemeral=True
            )

        m = await inter.followup.send("Mention first user.", ephemeral=True)
        try:
            first_msg: discord.Message = await self.bot.wait_for(
                "message", check=lambda msg: msg.author.id == inter.user.id, timeout=30
            )
            await first_msg.delete()

        except asyncio.TimeoutError:
            await m.edit(content="Timed out. Please try again later.", ephemeral=True)

        if not first_msg.mentions:
            await m.edit(content="You didn't mention first user.")

        first_user: discord.User = first_msg.mentions[0]

        _slots = await self.tourney.assigned_slots.filter(
            Q(leader_id=first_user.id) | Q(members__contains=first_user.id)
        ).order_by("num")

        if not _slots:
            return await inter.followup.send(
                f"{first_user.mention} don't have any slot in {self.tourney}.", ephemeral=True
            )

        first_slot = None
        if len(_slots) == 1:
            first_slot = _slots[0]

        else:
            cancel_view = BaseSelector(
                inter.user.id,
                TCancelSlotSelector,
                bot=self.bot,
                slots=_slots,
                placeholder=f"Select a slot of {str(first_user)}",
            )

            await inter.followup.send(
                f"{first_user.mention} has the following slots in {self.tourney}:", view=cancel_view, ephemeral=True
            )
            await cancel_view.wait()

            if cancel_view.custom_id:
                first_slot = await TMSlot.get(pk=cancel_view.custom_id)

        if not first_slot:
            return

        m = await inter.followup.send("Mention second user.", ephemeral=True)
        try:
            second_msg: discord.Message = await self.bot.wait_for(
                "message", check=lambda msg: msg.author.id == inter.user.id, timeout=30
            )
            await second_msg.delete()

        except asyncio.TimeoutError:
            await m.edit(content="Timed out. Please try again later.")

        if not second_msg.mentions:
            await m.edit(content="You didn't mention second user.")

        second_user: discord.User = second_msg.mentions[0]
        if second_user == first_user:
            return await inter.followup.send("You can't mention the same user twice.")

        _slots = await self.tourney.assigned_slots.filter(
            Q(leader_id=second_user.id) | Q(members__contains=second_user.id)
        ).order_by("num")

        if not _slots:
            return await inter.followup.send(
                f"{second_user.mention} don't have any slot in {self.tourney}.", ephemeral=True
            )

        second_slot = None
        if len(_slots) == 1:
            second_slot = _slots[0]

        else:
            cancel_view = BaseSelector(
                inter.user.id,
                TCancelSlotSelector,
                bot=self.bot,
                slots=_slots,
                placeholder=f"Select a slot of {str(second_user)}",
            )

            await inter.followup.send(
                f"{second_user.mention} has the following slots in {self.tourney}:", view=cancel_view, ephemeral=True
            )
            await cancel_view.wait()

            if cancel_view.custom_id:
                second_slot = await TMSlot.get(pk=cancel_view.custom_id)

        if not second_slot:
            return

        await TMSlot.get(pk=first_slot.id).update(num=second_slot.num)
        await TMSlot.get(pk=second_slot.id).update(num=first_slot.num)

        await inter.followup.send(
            f"{emote.check} | Groups were swapped. Press 'Refresh' button under grouplist.", ephemeral=True
        )
