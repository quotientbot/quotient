from core import Cog, Quotient
from discord.ext import tasks
import models
import config


class QuoTasks(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.insert_guilds.start()
        self.find_new_voters.start()

    @tasks.loop(count=1)
    async def insert_guilds(self):
        query = "INSERT INTO guild_data (guild_id , prefix , embed_color , embed_footer , bot_master , muted_members ,disabled_channels , disabled_users , disabled_commands , censored) VALUES ($1 , $2 , $3, $4, $5, $6 , $7, $8, $9 ,$10) ON CONFLICT DO NOTHING"
        for guild in self.bot.guilds:
            await self.bot.db.execute(
                query,
                guild.id,
                config.PREFIX,
                config.COLOR,
                config.FOOTER,
                [],
                [],
                [],
                [],
                [],
                [],
            )

    @tasks.loop(seconds=15)
    async def find_new_voters(self):
        records = await models.Votes.filter(is_voter=True, notified=False)
        if not len(records):
            return

        for record in records:
            self.bot.dispatch("vote", record)

    def cog_unload(self):
        self.find_new_voters.cancel()

    @insert_guilds.before_loop
    @find_new_voters.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()
