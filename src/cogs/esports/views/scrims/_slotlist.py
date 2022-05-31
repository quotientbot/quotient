from __future__ import annotations

from core import Context
import discord

from models import Scrim

__all__ = ("ManageSlotlist",)


class ManageSlotlist(discord.ui.Select):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(
            placeholder="Select an option to manage slotlist.",
            options=[
                discord.SelectOption(
                    label="Repost Slotlist",
                    emoji="<:re:980844295303098438>",
                    description="Respost slotlist to a channel",
                    value="repost",
                ),
                discord.SelectOption(
                    label="Change Design",
                    description="Design slotlist of any scrim.",
                    emoji="<:settings:980844348159688706>",
                    value="format",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        if (selected := self.values[0]) == "repost":
            ...

        elif selected == "format":
            ...
