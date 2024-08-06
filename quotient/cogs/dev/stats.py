from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import asyncio
import io
import os
import sys
import textwrap
import traceback
from datetime import timedelta

import discord
import psutil
from discord import app_commands
from discord.ext import commands, tasks
from humanize import precisedelta

from quotient.cogs.dev.consts import MOD_ROLE_IDS, PRIVATE_GUILD_IDS
from quotient.lib.msgs import TabularData
from quotient.models.others.cmds import Command


class DevStats(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.process = psutil.Process()
        self._batch_lock = asyncio.Lock()
        self._cmds_batch: list[Command] = []
        self.bulk_insert_loop.start()

        self.bot.on_error = self.on_error
        self.bot.old_tree_error = self.bot.tree.on_error
        self.bot.tree.on_error = self.on_app_command_error

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.id == self.bot.owner_id and not any(role_id in interaction.user._roles for role_id in MOD_ROLE_IDS):
            await interaction.response.send_message(
                "https://tenor.com/view/pedro-monkey-puppet-meme-awkward-gif-15268759", ephemeral=True
            )
            return False

        return True

    def cog_unload(self):
        self.bulk_insert_loop.stop()

    @tasks.loop(seconds=10.0)
    async def bulk_insert_loop(self):
        async with self._batch_lock:
            if not self._cmds_batch:
                return

            await Command.bulk_create(self._cmds_batch)
            self.bot.logger.info(f"Registered {len(self._cmds_batch)} command(s) into the database.")

            self._cmds_batch.clear()

    async def register_command(self, ctx: commands.Context) -> None:
        if ctx.command is None:
            return

        command = ctx.command.qualified_name
        is_app_command = ctx.interaction is not None

        message = ctx.message

        destination = f"#{message.channel} ({message.guild})"
        guild_id = ctx.guild.id

        if ctx.interaction and ctx.interaction.command:
            content = f"/{ctx.interaction.command.qualified_name}"
        else:
            content = message.content

        self.bot.logger.info(f"{message.created_at}: {message.author} in {destination}: {content}")
        async with self._batch_lock:
            self._cmds_batch.append(
                Command(
                    guild_id=guild_id,
                    channel_id=ctx.channel.id,
                    author_id=ctx.author.id,
                    prefix=ctx.prefix,
                    name=command,
                    failed=ctx.command_failed,
                    app_command=is_app_command,
                )
            )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        await self.register_command(ctx)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        command = interaction.command
        # Check if a command is found and it's not a hybrid command
        # Hybrid commands are already counted via on_command_completion
        if (
            command is not None
            and interaction.type is discord.InteractionType.application_command
            and not command.__class__.__name__.startswith("Hybrid")  # Kind of awful, but it'll do
        ):
            ctx = await self.bot.get_context(interaction)
            ctx.command_failed = interaction.command_failed or ctx.command_failed
            await self.register_command(ctx)

    async def send_guild_stats(self, e: discord.Embed, guild: discord.Guild):
        e.add_field(name="Name", value=guild.name)
        e.add_field(name="ID", value=guild.id)
        e.add_field(name="Shard ID", value=guild.shard_id or "N/A")
        e.add_field(name="Owner", value=f"{guild.owner} (ID: {guild.owner_id})")

        bots = sum(m.bot for m in guild.members)
        total = guild.member_count or 1
        e.add_field(name="Members", value=str(total))
        e.add_field(name="Bots", value=f"{bots} ({bots/total:.2%})")

        if guild.icon:
            e.set_thumbnail(url=guild.icon.url)

        if guild.me:
            e.timestamp = guild.me.joined_at

        await self.bot.logs_webhook.send(embed=e, username=self.bot.user.name, avatar_url=self.bot.user.default)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        e = discord.Embed(colour=0x53DDA4, title="New Guild")  # green colour
        await self.send_guild_stats(e, guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        e = discord.Embed(colour=0xDD5F53, title="Left Guild")  # red colour
        await self.send_guild_stats(e, guild)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        await self.register_command(ctx)
        if not isinstance(error, (commands.CommandInvokeError, commands.ConversionError)):
            return

        error = error.original
        if isinstance(error, (discord.Forbidden, discord.NotFound)):
            return

        e = discord.Embed(title="Command Error", colour=0xCC3366)
        e.add_field(name="Name", value=ctx.command.qualified_name)
        e.add_field(name="Author", value=f"{ctx.author} (ID: {ctx.author.id})")

        fmt = f"Channel: {ctx.channel} (ID: {ctx.channel.id})"
        if ctx.guild:
            fmt = f"{fmt}\nGuild: {ctx.guild} (ID: {ctx.guild.id})"

        e.add_field(name="Location", value=fmt, inline=False)
        e.add_field(name="Content", value=textwrap.shorten(ctx.message.content, width=512))

        exc = "".join(traceback.format_exception(type(error), error, error.__traceback__, chain=False))
        e.description = f"```py\n{exc}\n```"
        e.timestamp = discord.utils.utcnow()
        await self.bot.logs_webhook.send(embed=e, username=self.bot.user.name, avatar_url=self.bot.user.default_avatar.url)

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError, /) -> None:
        command = interaction.command
        error = getattr(error, "original", error)

        if isinstance(error, (discord.Forbidden, discord.NotFound)):
            return

        e = discord.Embed(title="App Command Error", colour=0xCC3366)

        if command is not None:
            if command._has_any_error_handlers():
                return

            e.add_field(name="Name", value=command.qualified_name)

        e.add_field(name="User", value=f"{interaction.user} (ID: {interaction.user.id})")

        fmt = f"Channel: {interaction.channel} (ID: {interaction.channel_id})"
        if interaction.guild:
            fmt = f"{fmt}\nGuild: {interaction.guild} (ID: {interaction.guild.id})"

        e.add_field(name="Location", value=fmt, inline=False)
        e.add_field(name="Namespace", value=" ".join(f"{k}: {v!r}" for k, v in interaction.namespace), inline=False)

        exc = "".join(traceback.format_exception(type(error), error, error.__traceback__, chain=False))
        e.description = f"```py\n{exc}\n```"
        e.timestamp = interaction.created_at

        try:
            await self.bot.logs_webhook.send(embed=e, username=self.bot.user.name, avatar_url=self.bot.user.default_avatar.url)
        except:
            pass

    async def on_error(self, event: str, *args: T.Any, **kwargs: T.Any) -> None:
        (exc_type, exc, tb) = sys.exc_info()
        # Silence command errors that somehow get bubbled up far enough here
        if isinstance(exc, commands.CommandInvokeError):
            return

        e = discord.Embed(title="Event Error", colour=0xA32952)
        e.add_field(name="Event", value=event)
        trace = "".join(traceback.format_exception(exc_type, exc, tb))
        e.description = f"```py\n{trace}\n```"
        e.timestamp = discord.utils.utcnow()

        args_str = ["```py"]
        for index, arg in enumerate(args):
            args_str.append(f"[{index}]: {arg!r}")
        args_str.append("```")
        e.add_field(name="Args", value="\n".join(args_str), inline=False)
        try:
            await self.bot.logs_webhook.send(embed=e)
        except:
            pass

    async def tabulate_query(self, inter: discord.Interaction, query: str, *args: T.Any):
        records = await self.bot.my_pool.fetch(query, *args)

        if len(records) == 0:
            return await inter.followup.send(embed=self.bot.error_embed("No results found."), ephemeral=True)

        headers = list(records[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in records)
        render = table.render()

        fmt = f"```\n{render}\n```"
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode("utf-8"))
            await inter.followup.send("Too many results...", file=discord.File(fp, "results.txt"))
        else:
            await inter.followup.send(fmt)

    # History commands

    history_grp = app_commands.Group(
        name="history",
        description="Shows Command History",
        guild_only=True,
        guild_ids=PRIVATE_GUILD_IDS,
    )

    _bot_grp = app_commands.Group(
        name="bot",
        description="Bot Health / Stats / etc.",
        guild_only=True,
        guild_ids=PRIVATE_GUILD_IDS,
    )

    @history_grp.command(name="all")
    async def history_list(self, inter: discord.Interaction):
        """List all commands history"""
        await inter.response.defer(thinking=True)
        query = """
                SELECT
                    CONCAT(
                        CASE WHEN app_command THEN '/' ELSE '' END,
                        name,
                        CASE WHEN failed THEN ' [!]' ELSE '' END
                    ) AS "command",
                    to_char((used_at AT TIME ZONE 'Asia/Kolkata'), 'Mon DD HH12:MI:SS AM') AS "invoked",
                    author_id,
                    guild_id
                FROM commands
                ORDER BY used_at DESC
                LIMIT 18;
                """
        await self.tabulate_query(inter, query)

    @history_grp.command(name="user")
    async def history_user(self, inter: discord.Interaction, user: discord.User):
        """List all commands history for a user"""
        await inter.response.defer(thinking=True)

        query = """
                SELECT
                    CONCAT(
                        CASE WHEN app_command THEN '/' ELSE '' END,
                        name,
                        CASE WHEN failed THEN ' [!]' ELSE '' END
                    ) AS "command",
                    guild_id,
                    to_char((used_at AT TIME ZONE 'Asia/Kolkata'), 'Mon DD HH12:MI:SS AM') AS "invoked"
                FROM commands
                WHERE author_id=$1
                ORDER BY used_at DESC
                LIMIT 20;
                """
        await self.tabulate_query(inter, query, user.id)

    @history_grp.command(name="guild")
    async def history_guild(self, inter: discord.Interaction, guild_id: str):
        """Command history for a guild."""
        await inter.response.defer(thinking=True)

        query = """SELECT
                        CONCAT(
                            CASE WHEN app_command THEN '/' ELSE '' END,
                            name,
                            CASE WHEN failed THEN ' [!]' ELSE '' END
                        ) AS "command",
                        channel_id,
                        author_id,
                        to_char((used_at AT TIME ZONE 'Asia/Kolkata'), 'Mon DD HH12:MI:SS AM') AS "invoked"
                   FROM commands
                   WHERE guild_id=$1
                   ORDER BY used_at DESC
                   LIMIT 18;
                """
        await self.tabulate_query(inter, query, int(guild_id))

    @history_grp.command(name="stats")
    async def history_stats(self, inter: discord.Interaction, days: int = 7):
        """Command history log for the last N days."""
        await inter.response.defer(thinking=True)

        query = """SELECT name, COUNT(*)
                   FROM commands
                   WHERE used_at > (CURRENT_TIMESTAMP - $1::interval)
                   GROUP BY name
                   ORDER BY 2 DESC
                """

        all_commands = {c.qualified_name: 0 for c in self.bot.walk_commands()}

        records = await self.bot.my_pool.fetch(query, timedelta(days=days))
        for name, uses in records:
            if name in all_commands:
                all_commands[name] = uses

        as_data = sorted(all_commands.items(), key=lambda t: t[1], reverse=True)
        table = TabularData()
        table.set_columns(["Command", "Uses"])
        table.add_rows(tup for tup in as_data)
        render = table.render()

        embed = discord.Embed(title="Summary", colour=self.bot.color)
        embed.set_footer(text="Since").timestamp = discord.utils.utcnow() - timedelta(days=days)

        top_ten = "\n".join(f"{command}: {uses}" for command, uses in records[:10])
        bottom_ten = "\n".join(f"{command}: {uses}" for command, uses in records[-10:])
        embed.add_field(name="Top 10", value=top_ten)
        embed.add_field(name="Bottom 10", value=bottom_ten)

        unused = ", ".join(name for name, uses in as_data if uses == 0)
        if len(unused) > 1024:
            unused = "Way too many..."

        embed.add_field(name="Unused", value=unused, inline=False)

        await inter.followup.send(embed=embed, file=discord.File(io.BytesIO(render.encode()), filename="full_results.txt"))

    # Bot health
    @_bot_grp.command(name="health")
    async def _bot_health(self, inter: discord.Interaction):
        """Various bot health monitoring tools."""

        # This uses a lot of private methods because there is no
        # clean way of doing this otherwise.

        HEALTHY = discord.Colour(value=0x43B581)
        UNHEALTHY = discord.Colour(value=0xF04947)
        WARNING = discord.Colour(value=0xF09E47)
        total_warnings = 0

        embed = discord.Embed(title="Bot Health Report", colour=HEALTHY)

        # Check the connection pool health.
        pool = self.bot.my_pool
        total_waiting = len(pool._queue._getters)  # type: ignore
        current_generation = pool._generation

        description = [
            f"Total `Pool.acquire` Waiters: {total_waiting}",
            f"Current Pool Generation: {current_generation}",
            f"Connections In Use: {len(pool._holders) - pool._queue.qsize()}",  # type: ignore
        ]

        questionable_connections = 0
        connection_value = []
        for index, holder in enumerate(pool._holders, start=1):
            generation = holder._generation
            in_use = holder._in_use is not None
            is_closed = holder._con is None or holder._con.is_closed()
            display = f"gen={holder._generation} in_use={in_use} closed={is_closed}"
            questionable_connections += any((in_use, generation != current_generation))
            connection_value.append(f"<Holder i={index} {display}>")

        joined_value = "\n".join(connection_value)
        embed.add_field(name="Connections", value=f"```py\n{joined_value}\n```", inline=False)

        spam_control = self.bot.spam_control
        being_spammed = [str(key) for key, value in spam_control._cache.items() if value._tokens == 0]

        description.append(f'Current Spammers: {", ".join(being_spammed) if being_spammed else "None"}')
        description.append(f"Questionable Connections: {questionable_connections}")

        total_warnings += questionable_connections
        if being_spammed:
            embed.colour = WARNING
            total_warnings += 1

        all_tasks = asyncio.all_tasks(loop=self.bot.loop)
        event_tasks = [t for t in all_tasks if "Client._run_event" in repr(t) and not t.done()]

        cogs_directory = os.path.dirname(__file__)
        tasks_directory = os.path.join("discord", "ext", "tasks", "__init__.py")
        inner_tasks = [t for t in all_tasks if cogs_directory in repr(t) or tasks_directory in repr(t)]

        bad_inner_tasks = ", ".join(hex(id(t)) for t in inner_tasks if t.done() and t._exception is not None)
        total_warnings += bool(bad_inner_tasks)
        embed.add_field(name="Inner Tasks", value=f'Total: {len(inner_tasks)}\nFailed: {bad_inner_tasks or "None"}')
        embed.add_field(name="Events Waiting", value=f"Total: {len(event_tasks)}", inline=False)

        command_waiters = len(self._cmds_batch)
        is_locked = self._batch_lock.locked()
        description.append(f"Commands Waiting: {command_waiters}, Batch Locked: {is_locked}")

        memory_usage = self.process.memory_full_info().uss / 1024**2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name="Process", value=f"{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU", inline=False)

        global_rate_limit = not self.bot.http._global_over.is_set()
        description.append(f"Global Rate Limit: {global_rate_limit}")

        if command_waiters >= 8:
            total_warnings += 1
            embed.colour = WARNING

        if global_rate_limit or total_warnings >= 9:
            embed.colour = UNHEALTHY

        embed.set_footer(text=f"{total_warnings} warning(s)")
        embed.description = "\n".join(description)
        await inter.response.send_message(embed=embed)

    @_bot_grp.command(name="uptime")
    async def _bot_uptime(self, inter: discord.Interaction):
        """Get the bot's uptime."""
        return await inter.response.send_message(
            f"Precise: {precisedelta(self.bot.current_time - self.bot.started_at)}",
            ephemeral=True,
        )
