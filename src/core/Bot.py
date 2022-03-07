from __future__ import annotations
from contextlib import suppress
import typing

if typing.TYPE_CHECKING:
    from ..cogs.reminder import Reminders


from discord import AllowedMentions, Intents
from discord.ext import commands
from tortoise import Tortoise

from datetime import datetime

from typing import Any, Callable, Coroutine, Dict, List, NoReturn, Optional, Union
from async_property import async_property
from datetime import datetime

import aiohttp, asyncio, os
import config as cfg

import itertools
import discord
import mystbin
import dbl
import time

import constants as csts

from .Context import Context
from .Help import HelpCommand
from .cache import CacheManager

intents = Intents.default()
intents.members = True


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["OMP_THREAD_LIMIT"] = "1"

__all__ = ("Quotient", "bot")


on_startup: List[Callable[["Quotient"], Coroutine]] = []


class Quotient(commands.AutoShardedBot):
    def __init__(self, **kwargs):
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

        asyncio.get_event_loop().run_until_complete(self.init_quo())
        self.loop = asyncio.get_event_loop()
        self.start_time = datetime.now(tz=csts.IST)
        self.cmd_invokes = 0
        self.seen_messages = 0
        self.binclient = mystbin.Client()

        self.persistent_views_added = False
        self.sio = None
        self.dblpy = dbl.DBLClient(self, self.config.DBL_TOKEN, autopost=True)

        self.lockdown: bool = False
        self.lockdown_msg: str = None
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.message_cache: Dict[int, Any] = {}
        # TODO: Use LRU caching

        for coro_func in on_startup:
            self.loop.create_task(coro_func(self))

    @on_startup.append
    async def __load_extensions(self):
        for ext in self.config.EXTENSIONS:
            self.load_extension(ext)
            print(f"Loaded extension: {ext}")


    @on_startup.append
    async def __load_presistent_views(self):

        from cogs.esports.views import ScrimsSlotmPublicView, TourneySlotManager, SlotlistEditButton
        from models import ScrimsSlotManager, Tourney, Scrim

        # Persistent views
        async for record in ScrimsSlotManager.all():
            self.add_view(ScrimsSlotmPublicView(self, record=record), message_id=record.message_id)

        async for tourney in Tourney.filter(slotm_message_id__isnull=False):
            self.add_view(TourneySlotManager(self, tourney=tourney), message_id=tourney.slotm_message_id)

        async for scrim in Scrim.filter(slotlist_message_id__isnull=False):
            self.add_view(SlotlistEditButton(self, scrim), message_id=scrim.slotlist_message_id)

        print("Persistent views: Loaded the f out of them")

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
        return "https://discord.gg/hxgevz9Z4e"

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

    async def get_prefix(self, message: discord.Message) -> str:
        """Get a guild's prefix"""
        if not message.guild:
            return

        prefix = None
        guild = self.cache.guild_data.get(message.guild.id)
        if guild:
            prefix = guild.get("prefix")

        else:
            self.cache.guild_data[message.guild.id] = {"prefix": "q", "color": self.color, "footer": cfg.FOOTER}

        prefix = prefix or "q"

        return commands.when_mentioned_or(
            *tuple("".join(chars) for chars in itertools.product(*zip(prefix.lower(), prefix.upper())))
        )(self, message)

    async def close(self) -> NoReturn:
        await super().close()
        await self.session.close()
        await Tortoise.close_connections()

    def get_message(self, message_id: int) -> discord.Message:
        """Gets the message from the cache"""
        return self._connection._get_message(message_id)

    async def process_commands(self, message: discord.Message):
        if message.content:
            ctx = await self.get_context(message, cls=Context)

            if ctx.command is None:
                return

            await self.invoke(ctx)

    async def on_message(self, message: discord.Message):
        self.seen_messages += 1

        if not message.guild or message.author.bot:
            return

        await self.process_commands(message)

    async def on_command(self, ctx: Context):
        self.cmd_invokes += 1
        await csts.show_tip(ctx)
        await self.db.execute("INSERT INTO user_data (user_id) VALUES ($1) ON CONFLICT DO NOTHING", ctx.author.id)

    async def on_ready(self):
        print(f"[Quotient] Logged in as {self.user.name}({self.user.id})")

    def embed(self, ctx: Context, **kwargs) -> discord.Embed:
        """This is how we deliver features like custom footer and custom color :)"""
        embed_color = self.cache.guild_data[ctx.guild.id]["color"]
        embed_footer = self.cache.guild_data[ctx.guild.id]["footer"]

        if embed_footer.strip().lower() == "none":
            embed_footer = discord.Embed.Empty

        embed = discord.Embed(**kwargs)
        embed.color = embed_color
        embed.set_footer(text=embed_footer)
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

        members = await guild.query_members(limit=1, user_ids=(member_id,), cache=True)

        if len(members) > 0:
            return members[0]

    @property
    def server(self) -> Optional[discord.Guild]:
        return self.get_guild(746337818388987967)

    @property
    def invite_url(self):
        return f"https://discord.com/oauth2/authorize?client_id={self.user.id}&scope=applications.commands%20bot&permissions=21175985838"

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
    async def getch(get_method, fetch_method, _id) -> Any:  # why does c have all the fun?
        try:
            _result = get_method(_id) or await fetch_method(_id)
        except (discord.HTTPException, discord.NotFound):
            return None
        else:
            return _result

    async def get_or_fetch_message(self, channel: discord.TextChannel, message_id: int) -> Optional[discord.Message]:
        # caching cause, due to rate limiting 50/1
        try:
            return self.message_cache[message_id]
            # scripting is always faster than `.get()`
        except KeyError:
            before = discord.Object(message_id + 1)
            after = discord.Object(message_id - 1)
            async for msg in channel.history(limit=1, before=before, after=after):
                if msg:
                    self.message_cache[msg.id] = msg
                    return msg

    async def send_message(self, channel_id, content, **kwargs):
        await self.http.send_message(channel_id, content, **kwargs)

    async def convey_important_message(
        self, guild: discord.Guild, text: str, *, view=None, title="\N{WARNING SIGN}__**IMPORTANT**__\N{WARNING SIGN}"
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
                content=", ".join(_roles[:2]) if _roles else guild.owner.mention,
                allowed_mentions=AllowedMentions(roles=True),
                view=view,
            )

        with suppress(discord.HTTPException):
            await guild.owner.send(embed=_e, view=view)


bot = Quotient()


@bot.before_invoke
async def bot_before_invoke(ctx: Context):
    if (_g := ctx.guild) != None and not _g.chunked:
        bot.loop.create_task(_g.chunk())
