from __future__ import annotations

import typing as T
from contextlib import suppress

import discord

from models import AssignedSlot, BanLog, Scrim

if T.TYPE_CHECKING:
    from core import Quotient

import asyncio
import random

from tortoise.exceptions import OperationalError

from utils import TimeText, emote

from .editor import *
from .select import BanOptions, prompt_slot_selection

__all__ = ("SlotlistEditButton",)


class SlotlistEditButton(discord.ui.View):
    message: discord.Message

    def __init__(self, bot: Quotient, scrim: Scrim):
        super().__init__(timeout=None)

        self.bot = bot
        self.scrim = scrim

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not any(
            (
                interaction.user.guild_permissions.manage_guild,
                "scrims-mod" in (_.name.strip().lower() for _ in interaction.user.roles),
            )
        ):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=("You need `manage server` permissions or `scrims-mod` role to edit this slotlist."),
                ),
                ephemeral=True,
            )

        return True

    @discord.ui.button(label="Edit", emoji="📝", style=discord.ButtonStyle.green, custom_id="scrim_slotlist_edit_b")
    async def edit_slotlist(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            await self.scrim.refresh_from_db()
        except OperationalError:
            await interaction.followup.send("This scrim has been deleted.", ephemeral=True)

        _view = ScrimsSlotlistEditor(
            self.bot, self.scrim, await self.scrim.slotlist_channel.fetch_message(self.scrim.slotlist_message_id)
        )
        embed = _view.initial_embed()
        _view.message = await interaction.followup.send(embed=embed, view=_view, ephemeral=True)

    @discord.ui.button(label="Punish", emoji="🛠️", style=discord.ButtonStyle.danger, custom_id="scrim_slotlist_ban_b")
    async def ban_slot(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)

        __slots = await self.scrim.assigned_slots.all().order_by("num")
        if not __slots:
            return await interaction.followup.send("No slot in the scrim to ban.", ephemeral=True)

        _v = await prompt_slot_selection(__slots, placeholder="Select the slots to ban the teams...", multiple=True)

        _e = discord.Embed(color=0x00FFB3, description="Kindly choose slots from the dropdown.")

        await interaction.followup.send(embed=_e, view=_v, ephemeral=True)

        await _v.wait()
        if slot_ids := _v.custom_id:
            _slots = await AssignedSlot.filter(pk__in=slot_ids)
            _e.description = "Enter the time & reason to ban the teams. (Time is optional)\n\nExamples:"
            _e.set_image(url="https://cdn.discordapp.com/attachments/782161513825042462/947436682800685056/banreason.gif")
            await interaction.followup.send(embed=_e, ephemeral=True)

            try:
                message: discord.Message = await self.bot.wait_for(
                    "message",
                    check=lambda x: x.author == interaction.user and x.channel == interaction.channel,
                    timeout=60,
                )

            except asyncio.TimeoutError:
                return await interaction.followup.send("Timed out", ephemeral=True)

            await message.delete()
            reason = await TimeText().convert(await self.bot.get_context(message), message.content)

            _v = BanOptions()
            await interaction.followup.send(embed=_v.initial_embed(), view=_v, ephemeral=True)
            await _v.wait()
            if _v.value:
                _e.title = "Banning teams..."
                _e.description = ""
                _e.set_image(url=None)

                m = await interaction.followup.send(embed=_e, ephemeral=True)

                for idx, _ in enumerate(_slots, start=1):
                    _e.description += f"`{idx}`: {emote.check} {await self.scrim.ban_slot(_,mod=interaction.user,reason=reason,ban_type=_v.value)}\n"
                    with suppress(discord.HTTPException):
                        await m.edit(embed=_e)
                        await asyncio.sleep(0.5)

                _e.title = "Banning Complete!"
                with suppress(discord.HTTPException):
                    await m.edit(embed=_e)

                if not await BanLog.get(guild_id=interaction.guild_id).exists():
                    if random.randint(1, 50) == 1:
                        _e = discord.Embed(
                            color=0x00FFB3,
                            description=(
                                "I see You don't have a public banlog channel in your server.\n\n"
                                "You can set it up with `qbanlog #channel`."
                            ),
                        )
                        return await interaction.followup.send(embed=_e, ephermeral=True)
