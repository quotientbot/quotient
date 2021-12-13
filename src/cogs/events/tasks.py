from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core import Quotient

from core import Cog

from discord.ext import tasks
import config
from models import Votes, Premium


class QuoTasks(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.insert_guilds.start()
        self.find_new_voters_and_premiums.start()

    @tasks.loop(count=1)
    async def insert_guilds(self):
        query = "INSERT INTO guild_data (guild_id , prefix , embed_color , embed_footer) VALUES ($1 , $2 , $3, $4) ON CONFLICT DO NOTHING"
        for guild in self.bot.guilds:
            await self.bot.db.execute(query, guild.id, config.PREFIX, config.COLOR, config.FOOTER)

    @tasks.loop(seconds=10)
    async def find_new_voters_and_premiums(self):  # is it a bad idea?
        """
        This task fetches if someone purchased premium or voted for Quotient
        """
        async for record in Votes.filter(is_voter=True, notified=False):
            self.bot.dispatch("vote", record)

        async for record in Premium.filter(is_done=True, is_notified=False):
            self.bot.dispatch("premium_purchase", record)

    def cog_unload(self):
        self.find_new_voters_and_premiums.stop()

    @insert_guilds.before_loop
    @find_new_voters_and_premiums.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()
