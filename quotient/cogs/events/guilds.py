from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from discord.ext import commands

from quotient.models.others.guild import Guild, create_guild_if_not_exists
from quotient.models.others.premium import GuildTier


class GuildEvents(commands.Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if self.bot.is_main_instance:
            await create_guild_if_not_exists(self.bot.my_pool, guild.id)

        else:  # If this is Quotient Pro bot:
            record = await Guild.get_or_none(pk=guild.id)

            if any([not record, record.tier == GuildTier.FREE]):
                return await guild.leave()

        self.bot.loop.create_task(guild.chunk())
