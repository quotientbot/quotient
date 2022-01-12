from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog
from models import AutoPurge, Timer, Snipe
from contextlib import suppress
from datetime import datetime, timedelta
from constants import IST

import discord


class AutoPurgeEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.loop.create_task(self.delete_older_snipes())

    async def delete_older_snipes(self):  # we delete snipes that are older than 10 days
        await self.bot.wait_until_ready()
        await Snipe.filter(delete_time__lte=(datetime.now(tz=IST) - timedelta(days=10))).delete()

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return
        channel = message.channel
        content = message.content if message.content else "*[Content Unavailable]*"

        await Snipe.update_or_create(
            channel_id=channel.id,
            defaults={"author_id": message.author.id, "content": content, "nsfw": channel.is_nsfw()},
        )

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or not message.channel.id in self.bot.cache.autopurge_channels:
            return

        record = await AutoPurge.get_or_none(channel_id=message.channel.id)
        if not record:
            return self.bot.cache.autopurge_channels.discard(message.channel.id)

        await self.bot.reminders.create_timer(
            datetime.now(tz=IST) + timedelta(seconds=record.delete_after),
            "autopurge",
            message_id=message.id,
            channel_id=message.channel.id,
        )

    @Cog.listener()
    async def on_autopurge_timer_complete(self, timer: Timer):

        message_id, channel_id = timer.kwargs["message_id"], timer.kwargs["channel_id"]

        check = await AutoPurge.get_or_none(channel_id=channel_id)
        if not check:
            return

        channel = check.channel
        if not channel:
            return

        message = channel.get_partial_message(message_id)
        with suppress(discord.NotFound, discord.Forbidden, discord.HTTPException):
            msg = await message.fetch()
            if not msg.pinned:
                await msg.delete()

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        if channel.id in self.bot.cache.autopurge_channels:
            await AutoPurge.filter(channel_id=channel.id).delete()
            self.bot.cache.autopurge_channels.discard(channel.id)
