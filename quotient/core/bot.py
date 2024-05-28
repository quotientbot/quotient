import logging
import os
from datetime import datetime

import aiohttp
import discord
import pytz
from discord.ext import commands

__all__ = ("Quotient",)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


class Quotient(commands.AutoShardedBot):
    session: aiohttp.ClientSession

    def __init__(self):
        super().__init__(
            command_prefix="q",
            enable_debug_events=True,
            intents=intents,
            strip_after_prefix=True,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, replied_user=True, users=True
            ),
        )

        self.seen_messages: int = 0

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

        for extension in os.getenv("EXTENSIONS").split(","):
            try:
                await self.load_extension(extension)
            except Exception as e:
                logging.exception("Failed to load extension %s.", extension)

    @property
    def current_time(self) -> datetime:
        return datetime.now(tz=pytz.timezone("Asia/Kolkata"))

    async def on_message(self, message: discord.Message) -> None:
        self.seen_messages += 1

        if message.guild is None or message.author.bot:
            return

        await self.process_commands(message)

    async def on_ready(self) -> None:
        logging.info("Ready: %s (ID: %s)", self.user, self.user.id)

    async def on_shard_resumed(self, shard_id: int) -> None:
        logging.info("Shard ID %s has resumed...", shard_id)

    async def start(self) -> None:
        await super().start(os.getenv("DISCORD_TOKEN"), reconnect=True)

    async def close(self) -> None:
        await super().close()

        if hasattr(self, "session"):
            await self.session.close()

        logging.info(f"{self.user} has logged out.")
