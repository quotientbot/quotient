from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from ..cogs.reminder import Reminders
from discord import AllowedMentions, Intents
from colorama import Fore, Style, init
from discord.ext import commands
from tortoise import Tortoise
from .Context import Context
from datetime import datetime
from utils import cache, IST
from typing import NoReturn, Optional
import aiohttp, asyncio, os
import config, asyncpg
from .Cog import Cog
import itertools
import traceback
import discord
import mystbin

init(autoreset=True)
intents = Intents.default()
intents.members = True


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
print(Fore.RED + "-----------------------------------------------------")


class Quotient(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            max_messages=1000,
            strip_after_prefix=True,
            case_insensitive=True,
            chunk_guilds_at_startup=False,
            allowed_mentions=AllowedMentions(everyone=False, roles=False, replied_user=True, users=True),
            activity=discord.Activity(type=discord.ActivityType.listening, name="qsetup | qhelp"),
            **kwargs,
        )
        asyncio.get_event_loop().run_until_complete(self.init_quo())
        self.loop = asyncio.get_event_loop()
        self.config = config
        self.color = config.COLOR
        self.start_time = datetime.now(tz=IST)
        self.cmd_invokes = 0
        self.binclient = mystbin.Client()
        self.lockdown = False
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        for ext in self.config.EXTENSIONS:
            try:
                self.load_extension(ext)
                print(Fore.GREEN + f"[EXTENSION] {ext} was loaded successfully!")
            except Exception as e:
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                tbe = "".join(tb) + ""
                print(Fore.RED + f"[WARNING] Could not load extension {ext}: {tbe}")
        print(Fore.RED + "-----------------------------------------------------")

    @property
    def db(self):
        return Tortoise.get_connection("default")._pool

    async def init_quo(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        await Tortoise.init(config.TORTOISE)
        await Tortoise.generate_schemas(safe=True)
        await cache(self)

        # TODO: create an autoclean timer or separate it per scrim maybe

        # Initializing Models (Assigning Bot attribute to all models)
        for mname, model in Tortoise.apps.get("models").items():
            model.bot = self

    async def get_prefix(self, message: discord.Message) -> str:
        if not message.guild:
            return

        if self.user.id == 765159200204128266:
            prefix = "!"
        else:
            prefix = self.guild_data[message.guild.id]["prefix"] or config.PREFIX

        return tuple("".join(chars) for chars in itertools.product(*zip(prefix.lower(), prefix.upper())))

    async def close(self) -> NoReturn:
        await super().close()
        await self.session.close()

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is None:
            return

        await self.invoke(ctx)

    async def on_command(self, ctx):
        self.cmd_invokes += 1

    async def on_ready(self) -> NoReturn:  # yes we love colors and colorama
        print(Fore.RED + "------------------------------------------------------")
        print(Fore.BLUE + f"[Quotient] Logged in as {self.user.name}({self.user.id})")
        print(Fore.BLUE + f"[Quotient] Currently in {len(self.guilds)} Guilds")
        print(Fore.BLUE + f"[Quotient] Connected to {len(self.users)} Users")
        print(Fore.CYAN + f"[Quotient] Spawned {len(self.shards)} Shards")

    def embed(self, ctx: Context, **kwargs) -> discord.Embed:
        """This is how we deliver features like custom footer and custom color :)"""
        embed_color = self.guild_data[ctx.guild.id]["color"]
        embed_footer = self.guild_data[ctx.guild.id]["footer"]
        kwargs.update(color=kwargs.pop("color", embed_color))

        embed = discord.Embed(**kwargs)
        embed.set_footer(text=embed_footer)
        return embed

    async def is_owner(self, user) -> bool:
        if await super().is_owner(user):
            return True

        return user.id in config.DEVS

    async def get_or_fetch_member(
        self,
        guild: discord.Guild,
        member_id: int,
    ) -> Optional[discord.Member]:
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

        if len(members) > 1:
            return members[0]

    @property
    def server(self) -> Optional[discord.Guild]:
        return self.get_guild(746337818388987967)

    @property
    def reminders(self) -> Reminders:  # since we use it a lot
        return self.get_cog("Reminders")
