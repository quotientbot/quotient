from __future__ import annotations

import typing
from cogs.esports.errors import TourneyError

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog, Context
from utils import exceptions
from constants import random_greeting
from discord.ext import commands

import discord


class Errors(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx: Context, err):

        ignored = (commands.CommandNotFound, commands.NoPrivateMessage, discord.Forbidden, discord.NotFound, TourneyError)

        if isinstance(err, ignored):
            return

        if isinstance(err, commands.NotOwner):
            return await ctx.send("Hmmm!😷")

        if isinstance(err, exceptions.QuotientError):
            return await ctx.error(err.__str__().format(ctx=ctx))

        if isinstance(err, commands.MissingRequiredArgument):
            return await ctx.send(
                f"{random_greeting()}, You missed the `{err.param.name}` argument.\n\nDo it like: `{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`"
            )

        if isinstance(err, commands.BadArgument):
            if isinstance(err, commands.MessageNotFound):
                return await ctx.error("Try the command again, and this time with a real message.")
            if isinstance(err, commands.MemberNotFound):
                return await ctx.error("Use the command again, and this time mention a real user.")
            if isinstance(err, commands.ChannelNotFound):
                return await ctx.error("Use the command again, and this time mention a real channel/category.")
            if isinstance(err, commands.RoleNotFound):
                await ctx.error("Try again and this time use a real role.")
            elif isinstance(err, commands.EmojiNotFound):
                await ctx.error("Try again and this time use a real emoji.")
            elif isinstance(err, commands.ChannelNotReadable):
                await ctx.error(
                    f"It looks like I do not have permissions to read the channel `{err.argument}`\n\nYou can fix it by going to channel settings and giving me permissions to view channel."
                )
            elif isinstance(err, commands.PartialEmojiConversionFailure):
                await ctx.error(f"The argument `{err.argument}` did not match the partial emoji format.")
            elif isinstance(err, commands.BadInviteArgument):
                await ctx.error(f"The invite that matched that argument was not valid or is expired.")
            elif isinstance(err, commands.BadBoolArgument):
                await ctx.error(f"The argument `{err.argument}` was not a valid True/False value.")
            elif isinstance(err, commands.BadColourArgument):
                await ctx.error(f"The argument `{err.argument}` was not a valid colour.")

            else:
                return await ctx.error(err)

        elif isinstance(err, commands.MissingRole):
            return await ctx.error(f"You need `{err.missing_role}` role to use this command.")

        elif isinstance(err, commands.MaxConcurrencyReached):
            return await ctx.error(f"This command is already running in this server. You have wait for it to finish.")

        elif isinstance(err, commands.CommandOnCooldown):
            if await ctx.bot.is_owner(ctx.author):
                return await ctx.reinvoke()
            return await ctx.send(f"You are in cooldown.\n\nTry again in `{err.retry_after:.2f}` seconds.")

        elif isinstance(err, commands.MissingPermissions):
            permissions = ", ".join([f"{permission}" for permission in err.missing_permissions])
            await ctx.error(f"You lack **`{permissions}`** permissions to run this command.")

        elif isinstance(err, commands.BotMissingPermissions):
            permissions = ", ".join([f"{permission}" for permission in err.missing_permissions])
            message = f"Unfortunately I am missing **`{permissions}`** permissions to run the command `{ctx.command}`.\nThis can be fixed by going to server settings > roles > Quotient and granting Quotient role **`{permissions}`** there."
            try:
                await ctx.send(message)
            except discord.Forbidden:
                try:
                    await ctx.author.send(f"Hey It looks like, I can't send messages in that channel.")
                except discord.Forbidden:
                    pass

            return

        else:  # will setup logging later
            raise err
