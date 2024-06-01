from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from datetime import timedelta

import discord
from core import Context
from discord.ext import commands
from models import AutoPurge, Timer

from .views import AutopurgeView


class Utility(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.Cog.listener(name="on_message")
    async def on_autopurge_message(self, message: discord.Message):
        if not message.channel.id in self.bot.cache.autopurge_channel_ids:
            return

        record = await AutoPurge.get_or_none(channel_id=message.channel.id)
        if not record:
            return self.bot.cache.autopurge_channel_ids.discard(message.channel.id)

        await self.bot.reminders.create_timer(
            self.bot.current_time + timedelta(seconds=record.delete_after),
            "autopurge",
            message_id=message.id,
            channel_id=message.channel.id,
        )

    @commands.Cog.listener()
    async def on_autopurge_timer_complete(self, timer: Timer):
        message_id, channel_id = timer.kwargs["message_id"], timer.kwargs["channel_id"]

        record = await AutoPurge.get_or_none(channel_id=channel_id)
        if not record:
            return

        channel = record.channel
        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
            if message and not message.pinned:
                await message.delete(delay=0, reason="AutoPurge is on this channel.")
        except discord.HTTPException:
            pass

    @commands.hybrid_command(name="autopurge", aliases=["ap"])
    async def autopurge_cmd(self, ctx: Context):
        v = AutopurgeView(self.bot, ctx)
        v.message = await ctx.send(embed=await v.initial_msg(), view=v)


async def setup(bot: Quotient):
    await bot.add_cog(Utility(bot))
