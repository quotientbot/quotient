from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import inspect
import itertools
import os
import time
from datetime import datetime

import discord
import psutil
import pygit2
from core import Context
from discord.ext import commands
from humanize import precisedelta

from quotient.lib import truncate_string
from quotient.models import Guild


class Miscellaneous(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.hybrid_command(aliases=("src",))
    async def source(self, ctx: Context, *, search: T.Optional[str]):
        """Refer to the source code of the bot commands."""
        source_url = "https://github.com/quotientbot/Quotient-Bot"
        command = ctx.bot.get_command(search)

        if search is None or command is None:
            return await ctx.send(f"<{source_url}>")

        src = command.callback.__code__
        filename = src.co_filename
        lines, firstlineno = inspect.getsourcelines(src)

        location = os.path.relpath(filename).replace("\\", "/")

        final_url = f"<{source_url}/blob/main/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await ctx.send(final_url)

    @commands.hybrid_command(aliases=("inv",))
    async def invite(self, ctx: Context):
        """Quotient Invite Links."""
        v = discord.ui.View(timeout=None)
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Invite Quotient (Free)",
                url=os.getenv("QUOTIENT_INVITE_LINK"),
                row=1,
            )
        )
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Invite Quotient Pro (Premium Only)",
                url=os.getenv("PRO_INVITE_LINK"),
                row=2,
            )
        )
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label="Join Support Server",
                url=os.getenv("SUPPORT_SERVER_LINK"),
                row=3,
            )
        )

        await ctx.reply(view=v)

    @commands.hybrid_command()
    async def contributors(self, ctx):
        """People who made Quotient Possible."""
        url = f"https://api.github.com/repos/quotientbot/Quotient-Bot/contributors"

        e = discord.Embed(
            title=f"Project Contributors",
            color=self.bot.color,
            timestamp=self.bot.current_time,
        )
        e.description = ""
        async with self.bot.session.get(url) as response:
            data = await response.json()
            for idx, contributor in enumerate(data, start=1):
                if contributor["type"] == "Bot":
                    continue

                e.description += f"`{idx:02}.` [{contributor['login']} ({contributor['contributions']})]({contributor['html_url']})\n"

        await ctx.reply(embed=e)

    @commands.hybrid_command()
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx: Context, *, new_prefix: str = None):
        """Change your server's prefix"""

        if not new_prefix:

            return await ctx.send(
                embed=self.bot.simple_embed(
                    "Current prefix of this server is `{0}`".format(self.bot.cache.prefixes.get(ctx.guild.id, self.bot.default_prefix))
                )
            )

        if len(new_prefix) > 5:
            return await ctx.reply(embed=self.bot.error_embed("Prefix cannot contain more than `5 characters`."))

        self.bot.cache.prefixes[ctx.guild.id] = new_prefix
        await Guild.filter(guild_id=ctx.guild.id).update(prefix=new_prefix)
        await ctx.reply(embed=self.bot.success_embed(f"Updated server prefix to: `{new_prefix}`"))

    @commands.hybrid_command()
    async def ping(self, ctx: Context):
        """Check how the bot is doing"""
        await ctx.send(f"Bot: `{round(self.bot.latency*1000, 2)} ms`, Database: `{await self.get_db_latency()}`")

    async def get_db_latency(self):
        t1 = time.perf_counter()
        await self.bot.my_pool.fetchval("SELECT 1;")
        t2 = time.perf_counter() - t1
        return f"{t2*1000:.2f} ms"

    @staticmethod
    def format_commit(commit: pygit2.Commit):  # source: R danny
        short, _, _ = commit.message.partition("\n")
        short_sha2 = commit.short_id
        commit_time = datetime.fromtimestamp(commit.commit_time)
        return f"[`{short_sha2}`](https://github.com/quotientbot/Quotient-Bot/commit/{commit.id}) {truncate_string(short,40)} ({discord.utils.format_dt(commit_time, 'R')})"

    def get_last_commits(self, count=3):
        repo = pygit2.Repository(".git")
        commits = list(itertools.islice(repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count))
        return "\n".join(self.format_commit(c) for c in commits)

    @commands.hybrid_command(aliases=("about",))
    async def stats(self, ctx: Context):
        """
        Get the bot's stats.
        """
        await ctx.defer()
        # Calculate DB Latency
        version = discord.__version__
        revision = self.get_last_commits()

        total_memory = psutil.virtual_memory().total >> 20
        used_memory = psutil.virtual_memory().used >> 20
        cpu_used = str(psutil.cpu_percent())

        total_members = sum(g.member_count for g in self.bot.guilds)
        cached_members = len(self.bot.users)

        cmd_stats = await self.bot.my_pool.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM commands) AS total_command_uses,
                (SELECT COUNT(*) FROM commands WHERE author_id = $1 AND guild_id = $2) AS user_invokes,
                (SELECT COUNT(*) FROM commands WHERE guild_id = $2) AS server_invokes
            """,
            ctx.author.id,
            ctx.guild.id,
        )
        owner = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, 548163406537162782)

        embed = discord.Embed(description="Latest Changes:\n" + revision)
        embed.title = "Quotient Official Support Server"
        embed.url = self.bot.config("SUPPORT_SERVER_LINK")
        embed.colour = self.bot.color
        embed.set_author(name=str(owner), icon_url=owner.display_avatar.url)

        guild_value = len(self.bot.guilds)

        embed.add_field(name="Servers", value=f"{guild_value:,} total\n{len(self.bot.shards)} shards")
        embed.add_field(
            name="Uptime",
            value=f"{precisedelta(self.bot.current_time - self.bot.started_at)}\n{self.bot.seen_messages:,} messages seen",
        )
        embed.add_field(name="Members", value=f"{total_members:,} Total\n{cached_members:,} cached")
        embed.add_field(name="System", value=f"**RAM**: {used_memory}/{total_memory} MB\n**CPU:** {cpu_used}% used.")
        embed.add_field(
            name="Commands Used",
            value=f"{cmd_stats['total_command_uses']:,} globally\n{cmd_stats['server_invokes']:,} in this server\n{cmd_stats['user_invokes']:,} by you.",
        )
        embed.add_field(
            name="Stats",
            value=f"Ping: {round(self.bot.latency * 1000, 2)}ms\nDb: {await self.get_db_latency()}",
        )

        embed.set_footer(text=f"Made with discord.py v{version}", icon_url="http://i.imgur.com/5BFecvA.png")

        await ctx.send(embed=embed, view=self.bot.contact_support_view())


async def setup(bot: Quotient):
    await bot.add_cog(Miscellaneous(bot))
