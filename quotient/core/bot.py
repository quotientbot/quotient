from __future__ import annotations

import logging
import os
import typing as T
from datetime import datetime

import aiohttp
import discord
import pytz
from asyncpg import Pool
from discord.ext import commands
from tortoise import Tortoise

if T.TYPE_CHECKING:
    from cogs.reminders import Reminders

from lib import CROSS, TICK

from .cache import CacheManager
from .ctx import Context

__all__ = ("Quotient",)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


log = logging.getLogger(os.getenv("INSTANCE_TYPE"))


def _prefix_callable(bot: Quotient, msg: discord.Message):
    bot_id = bot.user.id

    base = [f"<@{bot_id}> ", f"<@!{bot_id}> "]
    base.append(bot.cache.prefixes.get(msg.guild.id, os.getenv("DEFAULT_PREFIX")))

    return base


class Quotient(commands.AutoShardedBot):

    session: aiohttp.ClientSession

    def __init__(self):
        super().__init__(
            command_prefix=_prefix_callable,
            enable_debug_events=True,
            intents=intents,
            strip_after_prefix=True,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, replied_user=True, users=True
            ),
        )

        self.seen_messages: int = 0
        self.logger: logging.Logger = log
        self.cache = CacheManager()

    async def setup_hook(self) -> None:
        self.session = aiohttp.ClientSession()

        await Tortoise.init(
            config={
                "use_tz": True,
                "timezone": "Asia/Kolkata",
                "connections": {
                    "quotient": {
                        "engine": "tortoise.backends.asyncpg",
                        "credentials": {
                            "database": os.getenv("QUOTIENT_DB_NAME"),
                            "host": os.getenv("QUOTIENT_DB_HOST"),
                            "password": os.getenv("QUOTIENT_DB_PASSWORD"),
                            "port": 5432,
                            "user": os.getenv("QUOTIENT_DB_USER"),
                        },
                    },
                    "pro": {
                        "engine": "tortoise.backends.asyncpg",
                        "credentials": {
                            "database": os.getenv("PRO_DB_NAME"),
                            "host": os.getenv("PRO_DB_HOST"),
                            "password": os.getenv("PRO_DB_PASSWORD"),
                            "port": 5432,
                            "user": os.getenv("PRO_DB_USER"),
                        },
                    },
                },
                "apps": {
                    "default": {
                        "models": ["models"],
                        "default_connection": os.getenv("INSTANCE_TYPE"),
                    },
                },
            }
        )
        log.info("Tortoise has been initialized.")
        await Tortoise.generate_schemas(safe=True)

        for model_name, model in Tortoise.apps.get("default").items():
            model.bot = self

        await self.cache.populate_internal_cache()
        log.info("Internal cache has been populated.")

        for extension in os.getenv("EXTENSIONS").split(","):
            try:
                await self.load_extension(extension)
            except Exception as _:
                log.exception("Failed to load extension %s.", extension)

    async def get_or_fetch_member(
        self, guild: discord.Guild, member_id: int
    ) -> discord.Member | None:
        """Looks up a member in cache or fetches if not found."""
        member = guild.get_member(member_id)
        if member is not None:
            return member

        shard = self.get_shard(guild.shard_id)

        if shard.is_ws_ratelimited():
            try:
                member = await guild.fetch_member(member_id)
            except discord.HTTPException:
                return None
            else:
                return member

        members = await guild.query_members(limit=1, user_ids=[member_id], cache=True)

        if len(members) > 0:
            return members[0]

        return None

    @property
    def current_time(self) -> datetime:
        return datetime.now(tz=pytz.timezone("Asia/Kolkata"))

    @property
    def my_pool(self) -> Pool:
        return Tortoise.get_connection(os.getenv("INSTANCE_TYPE"))._pool

    @property
    def quotient_pool(self) -> Pool:
        return Tortoise.get_connection("quotient")._pool

    @property
    def pro_pool(self) -> Pool:
        return Tortoise.get_connection("pro")._pool

    @property
    def reminders(self) -> T.Optional[Reminders]:
        return self.get_cog("Reminders")

    @property
    def color(self) -> int:
        return int(os.getenv("DEFAULT_COLOR"))

    @property
    def default_prefix(self) -> str:
        return os.getenv("DEFAULT_PREFIX")

    def config(self, key: str) -> str | None:
        return os.getenv(key)

    def get_message(self, message_id: int) -> T.Optional[discord.Message]:
        """Gets the message from the cache"""
        return self._connection._get_message(message_id)

    def simple_embed(self, description: str, title: str = None) -> discord.Embed:
        return discord.Embed(color=self.color, description=description, title=title)

    def success_embed(self, description: str, title: str = None) -> discord.Embed:
        return discord.Embed(
            color=self.color,
            description=TICK + " | " + description,
            title=title,
        )

    def error_embed(self, description: str, title: str = None) -> discord.Embed:
        return discord.Embed(
            color=discord.Color.red(),
            description=CROSS + " | " + description,
            title=title,
        )

    async def process_commands(self, message: discord.Message):

        ctx = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_message(self, message: discord.Message) -> None:
        self.seen_messages += 1

        if any(
            [
                message.author.bot,
                message.guild is None,
                message.content in (None, ""),
            ]
        ):
            return

        await self.process_commands(message)

    async def on_ready(self) -> None:
        log.info("Ready: %s (ID: %s)", self.user, self.user.id)

    async def on_shard_resumed(self, shard_id: int) -> None:
        log.info("Shard ID %s has resumed...", shard_id)

    async def start(self) -> None:
        await super().start(os.getenv("DISCORD_TOKEN"), reconnect=True)

    async def close(self) -> None:
        await super().close()

        if hasattr(self, "session"):
            await self.session.close()

        log.info(f"{self.user} has logged out.")

        await Tortoise.close_connections()
        log.info("Tortoise connections have been closed.")
