from __future__ import annotations

from core import Context
import discord

from utils import regional_indicator as ri, inputs, truncate_string, emote

from ._base import ScrimsButton
from contextlib import suppress

from discord import Interaction


class SetName(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class RegChannel(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SlotChannel(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SetRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SetMentions(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class TotalSlots(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class OpenTime(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SetEmojis(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class Discard(ScrimsButton):
    def __init__(self, ctx: Context, label="Back"):
        super().__init__(style=discord.ButtonStyle.red, label=label)
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SaveScrim(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(style=discord.ButtonStyle.green, label="Save")
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
