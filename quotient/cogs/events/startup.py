from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from discord.ext import commands, tasks


class StartupEvents(commands.Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

        if self.bot.config("INSTANCE_TYPE") == "quotient":
            self.insert_new_guilds_in_db.start()

    def cog_unload(self):
        self.insert_new_guilds_in_db.cancel()

    @tasks.loop(count=1)
    async def insert_new_guilds_in_db(self):
        prefix = self.bot.config("DEFAULT_PREFIX")

        await self.bot.quotient_pool.executemany(
            "INSERT INTO guilds (guild_id, prefix) VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING",
            [(guild.id, prefix) for guild in self.bot.guilds],
        )

    @insert_new_guilds_in_db.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
