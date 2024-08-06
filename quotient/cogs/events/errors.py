from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from quotient.core import Quotient, Context

import discord
from discord.ext import commands


class ErrorHandler(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, err: commands.CommandError):
        ignored = (commands.CommandNotFound, commands.NotOwner, discord.NotFound, discord.Forbidden)

        if isinstance(err, ignored):
            return

        if isinstance(err, commands.MissingRequiredArgument | commands.TooManyArguments | commands.BadUnionArgument):
            return await ctx.send(
                embed=self.bot.error_embed(
                    f"Use the command properly: `{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`"
                ),
                view=self.bot.contact_support_view(),
            )

        elif isinstance(err, commands.BadArgument):
            if isinstance(err, commands.MemberNotFound):
                return await ctx.send(embed=self.bot.error_embed("Use the command again, and mention a real user."))
            if isinstance(err, commands.ChannelNotFound):
                return await ctx.send(embed=self.bot.error_embed("Use the command again, and mention a real channel."))
            if isinstance(err, commands.RoleNotFound):
                await ctx.send(embed=self.bot.error_embed("Use the command again, and mention a real role."))
            elif isinstance(err, commands.ChannelNotReadable):
                await ctx.send(
                    embed=self.bot.error_embed(
                        f"It looks like I do not have permissions to read the channel `{err.argument}`\n\nYou can fix it by going to channel settings and giving me permissions to view channel."
                    )
                )
            else:
                return await ctx.send(embed=self.bot.error_embed(err), view=self.bot.contact_support_view())

        elif isinstance(err, commands.CommandOnCooldown):
            return await ctx.send(
                embed=self.bot.error_embed(f"You hit the cooldown buddy.\n**Try again in `{err.retry_after:.2f}` seconds.**")
            )

        elif isinstance(err, commands.MissingPermissions):
            permissions = ", ".join(
                [f"{permission.replace('_', ' ').replace('guild', 'server').title()}" for permission in err.missing_permissions]
            )
            await ctx.send(
                embed=self.bot.error_embed(f"You lack **`{permissions}`** permissions to run this command."),
                view=self.bot.contact_support_view(),
            )

        elif isinstance(err, commands.BotMissingPermissions):
            permissions = ", ".join(
                [f"{permission.replace('_', ' ').replace('guild', 'server').title()}" for permission in err.missing_permissions]
            )
            try:
                await ctx.send(
                    embed=self.bot.error_embed(
                        f"Unfortunately I am missing **`{permissions}`** permissions to run the command `{ctx.command}`."
                    ),
                    view=self.bot.contact_support_view(),
                )
            except discord.Forbidden:
                pass

        elif isinstance(err, commands.CheckFailure):
            pass

        else:
            await ctx.send(embed=self.bot.error_embed(f"An error occurred: `{err}`"), view=self.bot.contact_support_view())
            self.bot.logger.error(f"An error occurred: {err}")
            raise err
