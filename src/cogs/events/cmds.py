from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import asyncio
from collections import defaultdict
from contextlib import suppress
from datetime import timedelta

import discord

from core import Cog, Context, cooldown
from models import ArrayRemove, Autorole, Commands


class UserCommandLimits(defaultdict):
    def __missing__(self, key):
        r = self[key] = cooldown.QuotientRatelimiter(2, 10)
        return r


class CmdEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.command_ratelimited_users = {}
        self.command_ratelimiter = UserCommandLimits(cooldown.QuotientRatelimiter)

    async def bot_check(self, ctx: Context):
        author = ctx.author
        message = ctx.message

        if author.id in self.bot.config.DEVS:
            return True

        if not ctx.guild:
            return False

        if author.id in self.bot.cache.blocked_ids or ctx.guild.id in self.bot.cache.blocked_ids:
            return False

        if retry_after := self.command_ratelimiter[message.author].is_ratelimited(message.author):
            if author.id in self.command_ratelimited_users:
                return

            self.command_ratelimited_users[author.id] = self.bot.current_time + timedelta(seconds=retry_after)
            self.bot.loop.create_task(self.remove_from_ratelimited_users(author.id, retry_after))

            await ctx.error(
                f"You are being ratelimited for using commands too fast. \n\n**Try again after `{retry_after:.2f} seconds`**."
            )
            return False

        if self.bot.lockdown is True:
            t = (
                "**Quotient is getting new features** 🥳\n"
                "Dear user, Quotient is updating and is not accepting any commands.\n"
                "It will back within **2 minutes**.\n"
            )

            if self.bot.lockdown_msg:
                t += f"\n\n**Message from developer:**\n{self.bot.lockdown_msg} ~ deadshot#7999"

            await ctx.error(t)
            return False

        return True

    async def remove_from_ratelimited_users(self, user_id: int, after: int):
        await asyncio.sleep(after)
        self.command_ratelimited_users.pop(user_id, None)

    @Cog.listener()
    async def on_command_completion(self, ctx: Context):
        if not ctx.command or not ctx.guild:
            return

        cmd = ctx.command.qualified_name

        await Commands.create(
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            user_id=ctx.author.id,
            cmd=cmd,
            prefix=ctx.prefix,
            failed=ctx.command_failed,
        )

    @Cog.listener(name="on_member_join")
    async def on_autorole(self, member: discord.Member):
        guild = member.guild

        with suppress(discord.HTTPException):
            record = await Autorole.get_or_none(guild_id=guild.id)
            if not record:
                return

            if not member.bot and record.humans:
                for role in record.humans:
                    try:
                        await member.add_roles(discord.Object(id=role), reason="Quotient's autorole")
                    except (discord.NotFound, discord.Forbidden):
                        await Autorole.filter(guild_id=guild.id).update(humans=ArrayRemove("humans", role))
                        continue

            elif member.bot and record.bots:
                for role in record.bots:
                    try:
                        await member.add_roles(discord.Object(id=role), reason="Quotient's autorole")
                    except (discord.Forbidden, discord.NotFound):
                        await Autorole.filter(guild_id=guild.id).update(bots=ArrayRemove("bots", role))
                        continue
            else:
                return
