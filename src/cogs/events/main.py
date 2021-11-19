from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from models import Guild, Timer
from core import Cog, Context

from contextlib import suppress
from constants import random_greeting, IST
import discord

from .utils import erase_guild
from datetime import datetime, timedelta
import re
import config

from cogs.premium.expire import activate_premium


class MainEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.loop.create_task(self.super_important_job())

    async def super_important_job(self):
        await self.bot.wait_until_ready()
        guild = await self.bot.getch(self.bot.get_guild, self.bot.fetch_guild, config.SERVER_ID)
        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())
        with suppress(AttributeError, discord.ClientException):
            await guild.get_channel(844178791735885824).connect()

    # incomplete?, I know
    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        with suppress(AttributeError):
            g, b = await Guild.get_or_create(guild_id=guild.id)
            self.bot.cache.guild_data[guild.id] = {
                "prefix": g.prefix,
                "color": g.embed_color or self.bot.color,
                "footer": g.embed_footer or config.FOOTER,
            }
            await guild.chunk()

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.bot.reminders.create_timer(
            datetime.now(tz=IST) + timedelta(minutes=20), "erase_guild", guild_id=guild.id
        )
        with suppress(AttributeError, KeyError):
            self.bot.cache.guild_data.pop(guild.id)

    @Cog.listener()
    async def on_erase_guild_timer_complete(self, timer: Timer):
        guild_id = timer.kwargs["guild_id"]
        guild = self.bot.get_guild(guild_id)
        if not guild:
            await erase_guild(guild_id)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if re.match(f"^<@!?{self.bot.user.id}>$", message.content):
            ctx = await self.bot.get_context(message)
            self.bot.dispatch("mention", ctx)

    @Cog.listener()
    async def on_mention(self, ctx: Context):
        prefix = self.bot.cache.guild_data[ctx.guild.id]["prefix"] or "q"
        await ctx.send(
            f"{random_greeting()} You seem lost. Are you?\n"
            f"Current prefix for this server is: `{prefix}`.\n\nUse it like: `{prefix}help`"
        )
