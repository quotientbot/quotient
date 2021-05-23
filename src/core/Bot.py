from discord import AllowedMentions, Intents
from colorama import Fore, Style, init
from discord.ext import commands
from tortoise import Tortoise
from .Context import Context
from datetime import datetime
from utils import cache, IST
from typing import NoReturn
import aiohttp, asyncio, os
import config, asyncpg

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
            command_prefix="!",
            intents=intents,
            max_messages=1000,
            strip_after_prefix=True,
            case_insensitive=True,
            chunk_guilds_at_startup=False,
            allowed_mentions=AllowedMentions(everyone=False, roles=False, replied_user=True, users=True),
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

        for ext in self.config.EXTENSIONS:
            try:
                self.load_extension(ext)
                print(Fore.GREEN + f"[EXTENSION] {ext} was loaded successfully!")
            except Exception as e:
                tb = traceback.format_exception(type(e), e, e.__traceback__)
                tbe = "".join(tb) + ""
                print(Fore.RED + f"[WARNING] Could not load extension {ext}: {tbe}")
        print(Fore.RED + "-----------------------------------------------------")

    async def init_quo(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.db = await asyncpg.create_pool(**config.POSTGRESQL)
        await Tortoise.init(config.TORTOISE)
        await Tortoise.generate_schemas(safe=True)
        await cache(self)

        # TODO: create an autoclean timer or separate it per scrim maybe

        # Initializing Models (Assigning Bot attribute to all models)
        for mname, model in Tortoise.apps.get("models").items():
            model.bot = self

    async def get_prefix(self, message: discord.Message) -> str:
        if message.guild is None:
            prefix = config.PREFIX

        else:
            try:
                prefix = self.guild_data[message.guild.id]["prefix"]
            except KeyError:
                prefix = config.PREFIX

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

    async def on_ready(self):  # yes we love colors and colorama
        print(Fore.RED + "------------------------------------------------------")
        print(Fore.BLUE + f"Logged in as {self.user.name}({self.user.id})")
        print(Fore.BLUE + f"Currently in {len(self.guilds)} Guilds")
        print(Fore.BLUE + f"Connected to {len(self.users)} Users")
        print(Fore.CYAN + f"Spawned {len(self.shards)} Shards")

    def embed(self, ctx: Context, **kwargs):
        """This is how we deliver features like custom footer and custom color :)"""
        embed_color = self.guild_data[ctx.guild.id]["color"]
        embed_footer = self.guild_data[ctx.guild.id]["footer"]
        kwargs.update(color=kwargs.pop("color", embed_color))

        embed = discord.Embed(**kwargs)
        embed.set_footer(text=embed_footer)

        return embed

    def get_cog(self, name):  # making cogs insensitive
        cogs = {key.lower() if isinstance(key, str) else key: value for key, value in self.cogs.items()}
        return cogs.get(name.lower())

    async def is_owner(self, user):
        if await super().is_owner(user):
            return True

        return user.id in config.DEVS

    async def get_or_fetch_member(self, guild: discord.Guild, member_id):
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
        if not members:
            return None
        return members[0]

    @property
    def server(self):
        return self.get_guild(746337818388987967)
