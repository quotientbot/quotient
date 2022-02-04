from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from prettytable import PrettyTable
from core import Cog, Context
from discord.ext import commands


from .helper import tabulate_query
from time import perf_counter as pf
from models import Commands, Guild
from utils import get_ipm, LinkButton, LinkType, Prompt, emote

import datetime
import discord

__all__ = ("Dev",)


class Dev(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.broadcast_channels = {
            "broadcast": 779229802975723531,
            "announcements": 829938693707399178,
            "changelogs": 829938782069063680,
            "status": 882510788215070720,
        }
        self.dead_id = 548163406537162782

    def cog_check(self, ctx: Context):
        return ctx.author.id in ctx.config.DEVS

    @property
    def dead(self):
        return self.bot.get_user(self.dead_id)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.id == self.dead_id:
            return

        if not message.channel or not message.channel.id in self.broadcast_channels.values():
            return

        prompt = Prompt(self.dead_id, 60)
        _m = await self.dead.send(f"Do you want to broadcast this message in {message.channel.mention}?", view=prompt)
        await prompt.wait()
        if not prompt.value:
            return await _m.edit("timed out", view=None)

        await _m.edit("Sending...", view=None)
        view = LinkButton([LinkType("More Info", self.bot.config.SERVER_LINK, emote.info)])
        content = message.clean_content + "\n\n- deadshot#7999, Team Quotient"

        success, failed = 0, 0

        _t1 = pf()
        async for guild in Guild.filter(private_channel__isnull=False):
            files = [await _.to_file(use_cached=True) for _ in message.attachments]

            try:
                channel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, guild.private_channel)
                await channel.send(content, files=files, view=view)
                success += 1
            except Exception as e:
                failed += 1

        await _m.edit(f"{success}:{failed} Time taken - {pf() - _t1:.3f}s.")

    @commands.command(hidden=True)
    async def cmds(self, ctx):
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
    async def command_history_for(self, ctx, days: typing.Optional[int] = 7, *, command: str):
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
    @commands.is_owner()
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
    async def command_history_cog(self, ctx, days: typing.Optional[int] = 7, *, cog: str = None):
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
