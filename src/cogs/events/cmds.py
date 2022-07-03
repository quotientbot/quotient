from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress

import discord

from core import Cog, Context
from models import ArrayRemove, Autorole, Commands


class CmdEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def bot_check(self, ctx: Context):
        if ctx.author.id in ctx.config.DEVS:
            return True

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

        if not ctx.guild:
            return False

        return True

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
