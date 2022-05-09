from __future__ import annotations

import discord

from models import Scrim


class BanSlot(discord.ui.Button):
    def __init__(self, scrim: Scrim):
        super().__init__(style=discord.ButtonStyle.danger, label="Punish", emoji="🛠️")

        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):
        ...
