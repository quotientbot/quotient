from core import Cog, Quotient
from discord.ext import tasks
import config


class QuoTasks(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.insert_guilds.start()

    @tasks.loop(count=1)
    async def insert_guilds(self):
        await self.bot.wait_until_ready()
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
