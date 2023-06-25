from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import asyncio
import datetime

import discord
from discord.ext import commands
from prettytable import PrettyTable

from core import Cog, Context
from models import BlockIdType, BlockList, Commands
from utils import get_ipm

from .helper import tabulate_query

__all__ = ("Dev",)


class Dev(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    def cog_check(self, ctx: Context):
        return ctx.author.id in ctx.config.DEVS

    @commands.group(hidden=True, invoke_without_command=True)
    async def bl(self, ctx: Context):
        """Blocklist commands."""
        await ctx.send_help(ctx.command)

    @bl.command(name="add")
    async def bl_add(self, ctx: Context, item: discord.User | int, *, reason: str = None):
        """Block a user or guild from using the bot."""
        block_id_type = BlockIdType.USER if isinstance(item, discord.User) else BlockIdType.GUILD
        block_id = item.id if isinstance(item, discord.User) else item

        record = await BlockList.get_or_none(block_id=block_id, block_id_type=block_id_type)
        if record:
            return await ctx.error(f"{item} is already blocked.")

        await BlockList.create(block_id=block_id, block_id_type=block_id_type, reason=reason)
        self.bot.cache.blocked_ids.add(block_id)
        await ctx.success(f"{item} has been blocked.")

    @bl.command(name="remove")
    async def bl_remove(self, ctx: Context, item: discord.User | int):
        """Unblock a user or guild from using the bot."""
        block_id = item.id if isinstance(item, discord.User) else item

        record = await BlockList.get_or_none(block_id=block_id)
        if not record:
            return await ctx.error(f"{item} is not blocked.")

        await record.delete()
        self.bot.cache.blocked_ids.remove(block_id)
        await ctx.success(f"{item} has been unblocked.")

    @commands.command(hidden=True)
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: T.Optional[T.Literal["~", "*", "^"]] = None,
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await self.bot.tree.sync()

            await ctx.send(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
            return

        ret = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    @commands.group(hidden=True, invoke_without_command=True)
    async def botupdate(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @botupdate.command(name="on")
    async def botmaintenance_on(self, ctx: Context, *, msg: str = None):
        self.bot.lockdown = True
        self.bot.lockdown_msg = msg
        await ctx.success("Now in maintenance mode")
        await asyncio.sleep(120)

        if not self.bot.lockdown:
            return await ctx.error("Lockdown mode has been cancelled")

        await ctx.success("Reloading...")
        self.bot.reboot()

    @botupdate.command(name="off")
    async def botmaintenance_off(self, ctx: Context):
        self.bot.lockdown, self.bot.lockdown_msg = False, None
        await ctx.success("Okay, stopped reload.")

    @commands.command(hidden=True)
    async def cmds(self, ctx: Context):
        total_uses = await Commands.all().count()

        records = await ctx.db.fetch(
            "SELECT cmd, COUNT(*) AS uses FROM commands GROUP BY cmd ORDER BY uses DESC LIMIT 15 "
        )

        table = PrettyTable()
        table.field_names = ["Command", "Invoke Count"]
        for record in records:
            table.add_row([record["cmd"], record["uses"]])

        table = table.get_string()
        embed = self.bot.embed(ctx, title=f"Command Usage ({total_uses})")
        embed.description = f"```{table}```"

        cmds = sum(1 for i in self.bot.walk_commands())

        embed.set_footer(text="Total Commands: {}  | Invoke rate per minute: {}".format(cmds, round(get_ipm(ctx.bot), 2)))

        await ctx.send(embed=embed)

    @commands.group(hidden=True, invoke_without_command=True, name="history")
    async def command_history(self, ctx):
        """Command history."""
        query = """SELECT
                        CASE failed
                            WHEN TRUE THEN cmd || ' [!]'
                            ELSE cmd
                        END AS "cmd",
                        to_char(used_at, 'Mon DD HH12:MI:SS AM') AS "invoked",
                        user_id,
                        guild_id
                   FROM commands
                   ORDER BY used_at DESC
                   LIMIT 15;
                """
        await tabulate_query(ctx, query)

    @command_history.command(name="for")
    async def command_history_for(self, ctx, days: T.Optional[int] = 7, *, command: str):
        """Command history for a command."""
        query = """SELECT *, t.success + t.failed AS "total"
                   FROM (
                       SELECT guild_id,
                              SUM(CASE WHEN failed THEN 0 ELSE 1 END) AS "success",
                              SUM(CASE WHEN failed THEN 1 ELSE 0 END) AS "failed"
                       FROM commands
                       WHERE cmd=$1
                       AND used_at > (CURRENT_TIMESTAMP - $2::interval)
                       GROUP BY guild_id
                   ) AS t
                   ORDER BY "total" DESC
                   LIMIT 30;
                """

        await tabulate_query(ctx, query, command, datetime.timedelta(days=days))

    @command_history.command(name="guild", aliases=["server"])
    async def command_history_guild(self, ctx, guild_id: int):
        """Command history for a guild."""
        query = """SELECT
                        CASE failed
                            WHEN TRUE THEN cmd || ' [!]'
                            ELSE cmd
                        END AS "cmd",
                        channel_id,
                        user_id,
                        used_at
                   FROM commands
                   WHERE guild_id=$1
                   ORDER BY used_at DESC
                   LIMIT 15;
                """
        await tabulate_query(ctx, query, guild_id)

    @command_history.command(name="user", aliases=["member"])
    async def command_history_user(self, ctx, user_id: int):
        """Command history for a user."""
        query = """SELECT
                        CASE failed
                            WHEN TRUE THEN cmd || ' [!]'
                            ELSE cmd
                        END AS "cmd",
                        guild_id,
                        used_at
                   FROM commands
                   WHERE user_id=$1
                   ORDER BY used_at DESC
                   LIMIT 20;
                """
        await tabulate_query(ctx, query, user_id)

    @command_history.command(name="cog")
    async def command_history_cog(self, ctx, days: T.Optional[int] = 7, *, cog: str = None):
        """Command history for a cog or grouped by a cog."""
        interval = datetime.timedelta(days=days)
        if cog is not None:
            cog = self.bot.get_cog(cog)
            if cog is None:
                return await ctx.send(f"Unknown cog: {cog}")

            query = """SELECT *, t.success + t.failed AS "total"
                       FROM (
                           SELECT command,
                                  SUM(CASE WHEN failed THEN 0 ELSE 1 END) AS "success",
                                  SUM(CASE WHEN failed THEN 1 ELSE 0 END) AS "failed"
                           FROM commands
                           WHERE cmd = any($1::text[])
                           AND used_at > (CURRENT_TIMESTAMP - $2::interval)
                           GROUP BY cmd
                       ) AS t
                       ORDER BY "total" DESC
                       LIMIT 30;
                    """
            return await tabulate_query(ctx, query, [c.qualified_name for c in cog.walk_commands()], interval)
