from __future__ import annotations

from typing import TYPE_CHECKING

from ...views.base import EsportsBaseView

if TYPE_CHECKING:
    from core import Quotient

import discord

from core import Context
from models import TagCheck


class TagCheckView(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx)

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    async def initial_embed(self):
        records = await TagCheck.filter(guild_id=self.ctx.guild.id)
        to_show = [f"`{idx}.` {_.__str__()}" for idx, _ in enumerate(records, start=1)]
        _m = "\n".join(to_show) if to_show else "```No TagCheck channels found.```"
        _e = discord.Embed(color=0x00FFB3, title="TagCheck Editor")
        _e.description = "**Current TagCheck channels:**\n" + _m
        _e.set_footer(text="Click Add Channel to set up a new TagCheck channel.")
        return _e

    @discord.ui.button(label="Add Channel", custom_id="add_tc_channel")
    async def add_tc_channel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

    @discord.ui.button(label="Remove Channel", custom_id="remove_tc_channel")
    async def remove_tc_channel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
