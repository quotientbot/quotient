from __future__ import annotations

import typing
from contextlib import suppress
from datetime import timedelta

if typing.TYPE_CHECKING:
    from core import Quotient

import asyncio

import discord
from discord.ext import tasks

from cogs.premium.views import PremiumView
from core import Cog, Context
from models import Guild
from utils import discord_timestamp


class ProCheckEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.__check_guilds.start()
        self.__prime_expire_reminders.start()

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        record = await self.bot.pool.fetchrow("SELECT * FROM guild_data WHERE guild_id = $1", guild.id)

        if not record or not record.get("is_premium", False):
            return await guild.leave()

        await Guild.get_or_create(guild_id=guild.id)

        await Guild.get(guild_id=guild.id).update(
            is_premium=True,
            premium_end_time=record["premium_end_time"],
            made_premium_by=record["made_premium_by"],
            private_channel=record["private_channel"],
        )

        self.bot.loop.create_task(guild.chunk())

    async def bot_check(self, ctx: Context) -> bool:
        if not ctx.guild:
            return False

        if not await self.bot.is_valid_guild(ctx.guild.id):
            await ctx.premium_mango("Your Premium has expired.")
            return False
        return True

    async def __match_guild_data(self, guild: discord.Guild):
        record = await self.bot.pool.fetchrow("SELECT * FROM guild_data WHERE guild_id = $1", guild.id)

        if not record or not record.get("is_premium", False):
            await Guild.filter(guild_id=guild.id).update(is_premium=False)
            return await guild.leave()

        await Guild.get_or_create(guild_id=guild.id)

        if not record.get("premium_end_time"):
            return

        await Guild.get(guild_id=guild.id).update(
            is_premium=True,
            premium_end_time=record["premium_end_time"],
            made_premium_by=record["made_premium_by"],
        )

        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())

    @tasks.loop(minutes=1)
    async def __check_guilds(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            await self.__match_guild_data(guild)

    @tasks.loop(hours=48)
    async def __prime_expire_reminders(self):
        await self.bot.wait_until_ready()

        await asyncio.sleep(900)

        async for _g in Guild.filter(is_premium=True, premium_end_time__lte=self.bot.current_time + timedelta(days=4)):
            guild = self.bot.get_guild(_g.guild_id)
            if not guild:
                continue

            _e = discord.Embed(color=self.bot.color, title="Quotient Prime Ending Soon")
            _e.description = (
                f"Quotient Premium subscription of {guild.name} is ending soon"
                f" ({discord_timestamp(_g.premium_end_time,'D')}) \n\n"
                "Kindly renew your subscription to continue using Quotient Premium features."
            )

            _v = PremiumView(label="Renew Premium")

            with suppress(discord.HTTPException):
                # if booster := _g.booster:
                # await booster.send(embed=_e, view=_v)
                if _ch := _g.private_ch:
                    await _ch.send(embed=_e, view=_v)

    def cog_unload(self) -> None:
        self.__check_guilds.cancel()
        self.__prime_expire_reminders.cancel()
