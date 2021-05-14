import discord, aiohttp, asyncio
from discord.ext import commands
from tortoise import Tortoise
import config, asyncpg


class Quotient(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix="!", *args, **kwargs)

        asyncio.get_event_loop().run_until_complete(self.init_quo())
        self.loop = asyncio.get_event_loop()
        self.config = config

    async def init_quo(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.db = await asyncpg.create_pool(**config.POSTGRESQL)
        await Tortoise.init(config.TORTOISE)
        await Tortoise.generate_schemas(safe=True)

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_ready(self):
        print("bot is ready!")
