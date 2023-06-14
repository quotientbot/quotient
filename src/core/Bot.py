from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    Iterable,
    List,
    Optional,
    Union,
)

if TYPE_CHECKING:
    from ..cogs.reminder import Reminders

import asyncio
import itertools
import os
import time
from datetime import datetime

import aiohttp
import config as cfg
import constants as csts
import dbl
import discord
import mystbin
from aiocache import cached
from async_property import async_property
from discord import AllowedMentions, Intents
from discord.ext import commands
from lru import LRU
from models import Guild
from tortoise import Tortoise

from .cache import CacheManager
from .Context import Context
from .Help import HelpCommand

intents = Intents.default()
intents.members = True
intents.message_content = True


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["OMP_THREAD_LIMIT"] = "1"

__all__ = ("Quotient", "bot")


on_startup: List[Callable[["Quotient"], Coroutine]] = []


class Quotient(commands.AutoShardedBot):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            max_messages=1000,
            strip_after_prefix=True,
            case_insensitive=True,
            help_command=HelpCommand(),
            chunk_guilds_at_startup=False,
            allowed_mentions=AllowedMentions(everyone=False, roles=False, replied_user=True, users=True),
            activity=discord.Activity(type=discord.ActivityType.listening, name="qsetup | qhelp"),
            **kwargs,
        )

        self.loop = asyncio.get_event_loop()
        self.start_time = datetime.now(tz=csts.IST)
        self.cmd_invokes = 0
        self.seen_messages = 0
        self.binclient = mystbin.Client()

        self.persistent_views_added = False
        self.sio = None
        self.dblpy = dbl.DBLClient(self, self.config.DBL_TOKEN, autopost=True)

        self.lockdown: bool = False
        self.lockdown_msg: Optional[str] = None
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.message_cache: Dict[int, Any] = LRU(1024)  # type: ignore

    @on_startup.append
    async def __load_extensions(self):
        for ext in self.config.EXTENSIONS:
            await self.load_extension(ext)
            print(f"Loaded extension: {ext}")

    @on_startup.append
    async def __load_presistent_views(self):
        from cogs.esports.views import (
            GroupRefresh,
            ScrimsSlotmPublicView,
            SlotlistEditButton,
            TourneySlotManager,
        )
        from models import Scrim, ScrimsSlotManager, TGroupList, Tourney

        # Persistent views
        async for record in ScrimsSlotManager.all():
            self.add_view(ScrimsSlotmPublicView(record), message_id=record.message_id)

        async for tourney in Tourney.filter(slotm_message_id__isnull=False):
            self.add_view(TourneySlotManager(self, tourney=tourney), message_id=tourney.slotm_message_id)

        async for scrim in Scrim.filter(slotlist_message_id__isnull=False):
            self.add_view(SlotlistEditButton(self, scrim), message_id=scrim.slotlist_message_id)

        async for record in TGroupList.all():
            self.add_view(GroupRefresh(), message_id=record.message_id)

        print("Persistent views: Loaded them too ")

    @on_startup.append
    async def __chunk_prime_guilds(self):
        from models import Guild

        async for g in Guild.filter(is_premium=True):
            if (_guild := self.get_guild(g.pk)) and not _guild.chunked:
                self.loop.create_task(_guild.chunk())

    @property
    def config(self) -> cfg:
        """import and return config.py"""
        return __import__("config")

    @property
    def db(self):
        """to execute raw queries"""
        return Tortoise.get_connection("default")._pool

    @property
    def prime_link(self):
        return "https://quotientbot.xyz/premium"

    @property
    def color(self):
        return self.config.COLOR

    def reboot(self):
        return os.system("pm2 reload quotient")

    async def init_quo(self):
        """Instantiating aiohttps ClientSession and telling tortoise to create relations"""
        self.session = aiohttp.ClientSession(loop=self.loop)
        await Tortoise.init(cfg.TORTOISE)
        await Tortoise.generate_schemas(safe=True)

        self.cache = CacheManager(self)
        await self.cache.fill_temp_cache()

        # Initializing Models (Assigning Bot attribute to all models)
        for mname, model in Tortoise.apps.get("models").items():
            model.bot = self

    async def setup_hook(self) -> None:
        await self.init_quo()
        for coro_func in on_startup:
            self.loop.create_task(coro_func(self))

    async def get_prefix(self, message: discord.Message) -> Union[str, Callable, List[str]]:
        """Get a guild's prefix"""
        if not message.guild:
            return commands.when_mentioned_or("q")(self, message)

        prefix = None
        guild = self.cache.guild_data.get(message.guild.id)
        if guild:
            prefix = guild.get("prefix")

        else:
            self.cache.guild_data[message.guild.id] = {
                "prefix": "q",
                "color": self.color,
                "footer": cfg.FOOTER,
            }

        prefix = prefix or "q"

        return commands.when_mentioned_or(
            *tuple("".join(chars) for chars in itertools.product(*zip(prefix.lower(), prefix.upper())))
        )(self, message)

    async def close(self) -> None:
        await super().close()

        if hasattr(self, "session"):
            await self.session.close()

        await Tortoise.close_connections()

    def get_message(self, message_id: int) -> Optional[discord.Message]:
        """Gets the message from the cache"""
        return self._connection._get_message(message_id)

    async def process_commands(self, message: discord.Message):
        if message.content and message.guild is not None:
            ctx = await self.get_context(message, cls=Context)

            if ctx.command is None:
                return

            await self.invoke(ctx)

    async def on_message(self, message: discord.Message):
        self.seen_messages += 1

        if message.guild is None or message.author.bot:
            return

        await self.process_commands(message)

    async def on_command(self, ctx: Context):
        self.cmd_invokes += 1
        await csts.show_tip(ctx)
        await csts.remind_premium(ctx)
        await self.db.execute("INSERT INTO user_data (user_id) VALUES ($1) ON CONFLICT DO NOTHING", ctx.author.id)

    async def on_ready(self):
        print(f"[Quotient] Logged in as {self.user.name}({self.user.id})")

    def embed(self, ctx: Context, **kwargs: Any) -> discord.Embed:
        """This is how we deliver features like custom footer and custom color :)"""
        embed_color = self.cache.guild_data[ctx.guild.id]["color"]
        embed_footer = self.cache.guild_data[ctx.guild.id]["footer"]

        if embed_footer.strip().lower() == "none":
            embed_footer = None

        embed = discord.Embed(**kwargs, color=embed_color).set_footer(text=embed_footer)
        return embed

    async def is_owner(self, user: Union[discord.Member, discord.User]) -> bool:
        if await super().is_owner(user):
            return True

        return user.id in cfg.DEVS

    async def get_or_fetch_member(self, guild: discord.Guild, member_id: int) -> Optional[discord.Member]:
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

    async def resolve_member_ids(
        self, guild: discord.Guild, member_ids: Iterable[int]
    ) -> AsyncGenerator[discord.Member, None]:
        """Bulk resolves member IDs to member instances, if possible."""

        needs_resolution = []
        for member_id in member_ids:
            member = guild.get_member(member_id)
            if member is not None:
                yield member
            else:
                needs_resolution.append(member_id)

        if not needs_resolution:
            return

        total_need_resolution = len(needs_resolution)
        if total_need_resolution == 1:
            shard: discord.ShardInfo = self.get_shard(guild.shard_id)  # type: ignore  # will never be None
            if shard.is_ws_ratelimited():
                try:
                    member = await guild.fetch_member(needs_resolution[0])
                except discord.HTTPException:
                    pass
                else:
                    yield member
            else:
                members = await guild.query_members(limit=1, user_ids=needs_resolution, cache=True)
                if members:
                    yield members[0]
        elif total_need_resolution <= 100:
            # Only a single resolution call needed here
            resolved = await guild.query_members(limit=100, user_ids=needs_resolution, cache=True)
            for member in resolved:
                yield member
        else:
            # We need to chunk these in bits of 100...
            for index in range(0, total_need_resolution, 100):
                to_resolve = needs_resolution[index : index + 100]
                members = await guild.query_members(limit=100, user_ids=to_resolve, cache=True)
                for member in members:
                    yield member

    @staticmethod
    @cached(ttl=60)
    async def is_premium_guild(guild_id: int) -> bool:
        return await Guild.filter(pk=guild_id, is_premium=True).exists()

    @property
    def server(self) -> Optional[discord.Guild]:
        return self.get_guild(746337818388987967)

    @property
    def invite_url(self) -> str:
        return discord.utils.oauth_url(
            self.user.id,
            permissions=discord.Permissions(536737213566),
            scopes=("bot", "applications.commands"),
            disable_guild_select=False,
        )

    @property
    def reminders(self) -> Reminders:  # since we use it a lot
        return self.get_cog("Reminders")

    @property
    def current_time(self):
        return datetime.now(tz=csts.IST)

    @async_property
    async def db_latency(self):
        t1 = time.perf_counter()
        await self.db.fetchval("SELECT 1;")
        t2 = time.perf_counter() - t1
        return f"{t2*1000:.2f} ms"

    @staticmethod
    async def getch(get_method: Callable, fetch_method: Callable, _id: int) -> Any:  # why does c have all the fun?
        try:
            _result = get_method(_id) or await fetch_method(_id)
        except (discord.HTTPException, discord.NotFound):
            return None
        else:
            return _result

    async def get_or_fetch_message(
        self,
        channel: discord.TextChannel,
        message_id: int,
        *,
        cache: bool = True,
        fetch: bool = True,
    ) -> Optional[discord.Message]:
        # caching cause, due to rate limiting 50/1
        if cache and (msg := self.get_message(message_id)):
            return msg
        try:
            return self.message_cache[message_id]
            # scripting is always faster than `.get()`
        except KeyError:
            pass
        before = discord.Object(message_id + 1)
        after = discord.Object(message_id - 1)
        if fetch:
            async for msg in channel.history(limit=1, before=before, after=after):
                self.message_cache[msg.id] = msg
                return msg

        return None

    async def send_message(self, channel_id: discord.abc.Snowflake, content, **kwargs: Any):
        await self.http.send_message(channel_id, content, **kwargs)

    async def convey_important_message(
        self,
        guild: discord.Guild,
        text: str,
        *,
        view=None,
        title="\N{WARNING SIGN}__**IMPORTANT**__\N{WARNING SIGN}",
    ):
        _e = discord.Embed(title=title, description=text)

        from models import Guild

        _g = await Guild.get(pk=guild.id)
        if (_c := _g.private_ch) and _c.permissions_for(guild.me).embed_links:
            _roles = [
                role.mention
                for role in guild.roles
                if all((role.permissions.administrator, not role.managed, role.members))
            ]
            await _c.send(
                embed=_e,
                content=", ".join(_roles[:2]) if _roles else getattr(guild.owner, "mention"),
                allowed_mentions=AllowedMentions(roles=True),
                view=view,
            )

        if guild.owner is not None:  # there is very little chance that `guild.owner` is None
            try:
                await guild.owner.send(embed=_e, view=view)
            except discord.Forbidden:
                return


bot = Quotient()


@bot.before_invoke
async def bot_before_invoke(ctx: Context):
    if ctx.guild is not None and not ctx.guild.chunked:
        bot.loop.create_task(ctx.guild.chunk())
