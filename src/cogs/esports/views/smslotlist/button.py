from __future__ import annotations

from models import Scrim
import discord

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from .editor import *

from tortoise.exceptions import OperationalError


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
    async def edit_slotlist(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await self.scrim.refresh_from_db()
        except OperationalError:
            await interaction.followup.send("This scrim has been deleted.", ephemeral=True)

        _view = ScrimsSlotlistEditor(
            self.bot, self.scrim, await self.scrim.slotlist_channel.fetch_message(self.scrim.slotlist_message_id)
        )
        embed = _view.initial_embed()
        _view.message = await interaction.followup.send(embed=embed, view=_view, ephemeral=True)
