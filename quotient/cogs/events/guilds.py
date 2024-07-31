from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from discord.ext import commands

from quotient.models import Guild


class GuildEvents(commands.Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if self.bot.is_main_instance:
            await self.bot.quotient_pool.execute(
                "INSERT INTO guilds (guild_id, prefix) VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING",
                guild.id,
                self.bot.config("DEFAULT_PREFIX"),
            )

        else:  # If this is Quotient Pro bot:
            record = await Guild.get_or_none(pk=guild.id)

            if any([not record, not record.is_premium]):
                await guild.leave()

        self.bot.loop.create_task(guild.chunk())
