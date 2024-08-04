from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from discord.ext import commands, tasks

from quotient.models.others.guild import bulk_create_guilds


class StartupEvents(commands.Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

        if self.bot.is_main_instance:
            self.insert_new_guilds_in_db.start()

    def cog_unload(self):
        self.insert_new_guilds_in_db.cancel()

    @tasks.loop(count=1)
    async def insert_new_guilds_in_db(self):
        await bulk_create_guilds(self.bot.my_pool, [guild.id for guild in self.bot.guilds])

    @insert_new_guilds_in_db.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
