from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress

import discord

from core import Cog
from models import Timer
from utils import discord_timestamp


class ReminderEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_reminder_timer_complete(self, timer: Timer):
        author_id, channel_id, message = timer.args

        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
        except discord.HTTPException:
            return

        guild_id = channel.guild.id if isinstance(channel, (discord.TextChannel, discord.Thread)) else "@me"
        message_id = timer.kwargs["message_id"]
        msg = f"{discord_timestamp(timer.created)}: {message}"

        jump_url = f"https://discord.com/channels/{guild_id}/{channel.id}/{message_id}"

        v = discord.ui.View(timeout=None)
        v.add_item(discord.ui.Button(label="Jump to Original Message", url=jump_url, style=discord.ButtonStyle.link))

        embed = discord.Embed(
            color=self.bot.color,
            title=f"Reminder #{timer.id}",
            description=msg,
            url=jump_url,
            timestamp=self.bot.current_time,
        )

        with suppress(discord.HTTPException, discord.Forbidden, AttributeError):
            await channel.send(f"<@{author_id}>", embed=embed, view=v)
