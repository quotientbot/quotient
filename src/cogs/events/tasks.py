from core import Cog, Quotient
from discord.ext import tasks


class QuoTasks(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        # self.insert_guilds.start()

    @tasks.loop(count=1)
    async def insert_guilds(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            await self.bot.db.execute("INSERT INTO guild_data (guild_id) VALUES ($1) ON CONFLICT DO NOTHING", guild.id)
