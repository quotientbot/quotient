from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import QuoView
from discord.ext import commands
from models import AutoPurge


class AutopurgeView(QuoView):
    def __init__(self, bot: Quotient, ctx: commands.Context):
        super().__init__(bot, ctx)

    async def initial_msg(self):
        records = await AutoPurge.filter(guild_id=self.ctx.guild.id)

        e = discord.Embed(
            color=self.bot.color,
            title="Auto Purge Settings",
        )
        e.description = (
            "Once a message is sent in the specified channel, "
            "the bot will wait for the designated time period before automatically deleting the message.\n\n"
        )

        if not records:
            e.description += "```Click 'Set New Channel' to get started.```"
            return e
        for idx, record in enumerate(records, start=1):
            e.description += f"`[{idx:02}]` {getattr(record.channel, 'mention', 'deleted-channel')}: \n"

        return e

    async def refresh_view(self):
        try:
            await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException as e:
            raise e

    @discord.ui.button(label="Set New Channel", style=discord.ButtonStyle.primary)
    async def set_ap_channel(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.send_message(
            embed=self.bot.error_embed("This feature is not yet implemented."),
            ephemeral=True,
        )

    @discord.ui.button(label="Remove Channel", style=discord.ButtonStyle.danger)
    async def del_ap_channel(self, inter: discord.Interaction, btnn: discord.ui.Button):
        await inter.response.send_message(
            embed=self.bot.error_embed("This feature is not yet implemented."),
            ephemeral=True,
        )
