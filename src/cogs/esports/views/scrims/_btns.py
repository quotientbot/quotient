from __future__ import annotations

from core import Context
import discord

from utils import regional_indicator as ri, inputs, truncate_string, emote

from ._base import ScrimsButton
from contextlib import suppress

from models import Scrim
from discord import Interaction


class SetName(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("Enter the new name of this scrim. (`Max 30 characters`)")
        name = await inputs.string_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)
        self.view.record.name = truncate_string(name, 30)

        await self.view.refresh_view()


class RegChannel(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("Mention the channel where you want to take registrations.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        if await Scrim.filter(registration_channel_id=channel.id).exists():
            return await self.ctx.error("That channel is already in use for another scrim.", 5)

        self.view.record.registration_channel_id = channel.id

        if not self.view.record.slotlist_channel_id:
            self.view.record.slotlist_channel_id = channel.id

        await self.view.refresh_view()


class SlotChannel(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("Mention the channel where you want me to post slotlist after registrations.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        self.view.record.slotlist_channel_id = channel.id

        await self.view.refresh_view()


class SetRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("Mention the role you want to give for correct registration.")
        role = await inputs.role_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        self.view.record.role_id = role.id

        await self.view.refresh_view()


class SetMentions(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("How many mentions are required for registration? (Max `10`)")
        self.view.record.required_mentions = await inputs.integer_input(self.ctx, delete_after=True, limits=(0, 10))
        await self.ctx.safe_delete(m)

        await self.view.refresh_view()


class TotalSlots(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("How many total slots are there? (Max `30`)")
        self.view.record.total_slots = await inputs.integer_input(self.ctx, delete_after=True, limits=(1, 30))
        await self.ctx.safe_delete(m)

        await self.view.refresh_view()


class OpenTime(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple(
            "At what time do you want me to open registrations daily?\n\nTime examples:",
            image="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
        )
        self.view.record.open_time = await inputs.time_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)

        await self.view.refresh_view()


class SetEmojis(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SetEmojis(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SetAutoclean(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class PingRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class OpenRole(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class OpenDays(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class MultiReg(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class MultiReg(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class MultiReg(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class TeamCompulsion(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class DuplicateTeam(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class DeleteReject(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class DeleteLate(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class SlotlistStart(ScrimsButton):
    def __init__(self, ctx: Context, letter: str):
        super().__init__(emoji=ri(letter))
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()


class Discard(ScrimsButton):
    def __init__(self, ctx: Context, label="Back"):
        super().__init__(style=discord.ButtonStyle.red, label=label)
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        from .main import ScrimsMain as SM

        self.view.stop()
        v = SM(self.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_embed(), view=v)


class SaveScrim(ScrimsButton):
    def __init__(self, ctx: Context):
        super().__init__(style=discord.ButtonStyle.green, label="Save Scrim", disabled=True)
        self.ctx = ctx

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
