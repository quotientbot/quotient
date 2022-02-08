from __future__ import annotations


from core import Context
import discord
from utils import regional_indicator as ri


class RegChannel(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=ri("A"))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        ...
