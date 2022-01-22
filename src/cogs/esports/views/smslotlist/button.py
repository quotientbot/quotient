from __future__ import annotations

from models import Scrim
import discord

from core import Context

from utils import emote

from .editor import *

from tortoise.exceptions import OperationalError


__all__ = ("SlotlistEditButton",)


class SlotlistEditButton(discord.ui.View):
    message: discord.Message

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(timeout=None)

        self.ctx = ctx
        self.scrim = scrim

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not any(
            (
                interaction.user.guild_permissions.manage_guild,
                "scrim-mod" in (_.name.strip().lower() for _ in interaction.user.roles),
            )
        ):
            return await interaction.followup.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=("You need `manage server` permissions or `scrim-mod` role to edit this slotlist."),
                )
            )

        return True

    @discord.ui.button(label="Edit", emoji="📝", style=discord.ButtonStyle.green)
    async def edit_slotlist(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await self.scrim.refresh_from_db()
        except OperationalError:
            await interaction.followup.send("This scrim has been deleted.", ephemeral=True)

        _view = ScrimsSlotlistEditor(self.ctx, self.scrim, self.message)
        embed = _view.initial_embed()
        _view.message = await interaction.followup.send(embed=embed, view=_view, ephemeral=True)
