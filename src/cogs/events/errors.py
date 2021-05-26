import discord
import traceback
from core import Cog, Quotient
from utils import exceptions, random_greeting
from discord.ext import commands
from discord.ext.commands import errors


class Errors(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_command_error(self, ctx, err):

        ignored = (
            commands.CommandNotFound,
            commands.NoPrivateMessage,
            discord.Forbidden,
        )

        if isinstance(err, ignored):
            return

        elif isinstance(err, commands.NotOwner):
            return await ctx.send("Hmmm!😷")

        elif isinstance(err, exceptions.NotSetup):
            return await ctx.error(
                f"This command requires you to have Quotient's private channel.\nKindly run `{ctx.prefix}setup` and try again."
            )

        elif isinstance(err, exceptions.InvalidColor):
            return await ctx.error(
                f"`{err}` doesn't seem to be a valid color, \nPick a shade from [here](https://www.google.com/search?q=color+picker)"
            )

        elif isinstance(err, exceptions.NotPremiumUser):
            return await ctx.error(
                f"This command requires you to be a premium user.\nCheckout Quotient Premium [here]({self.bot.config.WEBSITE}/premium)"
            )

        elif isinstance(err, exceptions.NotPremiumGuild):
            return await ctx.error(
                f"This command requires this server to be premium.\n\nCheckout Quotient Premium [here]({self.bot.config.WEBSITE}/premium)"
            )

        elif isinstance(err, exceptions.InputError):
            return await ctx.error(err)

        elif isinstance(err, exceptions.SMNotUsable):
            return await ctx.error(
                f"You need either the `scrims-mod` role or `manage_guild` permissions to use scrims manager."
            )

        elif isinstance(err, exceptions.TMNotUsable):
            return await ctx.error(
                f"You need either the `tourney-mod` role or `manage_guild` permissions to use tourney manager."
            )

        elif isinstance(err, exceptions.PastTime):
            return await ctx.send(
                f"The time you entered seems to be in past.\n\nKindly try again, use times like: `tomorrow` , `friday 9pm`"
            )

        elif isinstance(err, exceptions.InvalidTime):
            return await ctx.send(f"The time you entered seems to be invalid.\n\nKindly try again.")

        elif isinstance(err, errors.MissingRequiredArgument):
            return await ctx.send(
                f'{random_greeting()}, You missed the `{err.param.name}` argument.\n\nDo it like: `{ctx.prefix}{(ctx.invoked_subcommand.full_parent_name + " " +ctx.invoked_subcommand.name) if ctx.invoked_subcommand else ctx.command.name} {(ctx.invoked_subcommand if ctx.invoked_subcommand else ctx.command).signature}`'
            )  # confused? me too

        elif isinstance(err, commands.BadArgument):
            if isinstance(err, commands.MessageNotFound):
                return await ctx.error("Try the command again, and this time with a real message.")
            elif isinstance(err, commands.MemberNotFound):
                return await ctx.error("Use the command again, and this time mention a real user.")
            elif isinstance(err, commands.ChannelNotFound):
                return await ctx.error("Use the command again, and this time mention a real channel/category.")
            elif isinstance(err, commands.RoleNotFound):
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

        elif isinstance(err, errors.CommandOnCooldown):
            is_owner = await ctx.bot.is_owner(ctx.author)
            if is_owner is True:
                return await ctx.reinvoke()
            await ctx.send(f"You are in cooldown.\n\nTry again in `{err.retry_after:.2f}` seconds.")
            return

        elif isinstance(err, commands.MissingPermissions):
            is_owner = await ctx.bot.is_owner(ctx.author)
            if is_owner is True:
                return await ctx.reinvoke()

            permissions = ", ".join([f"{permission}" for permission in err.missing_perms])
            await ctx.error(f"You lack **`{permissions}`** permissions to run this command.")

        elif isinstance(err, commands.BotMissingPermissions):
            permissions = ", ".join([f"{permission}" for permission in err.missing_perms])
            message = f"Unfortunately I am missing **`{permissions}`** permissions to run the command `{ctx.command}`.\nYou can fix this by going to server settings > roles > Quotient and granting Quotient role **`{permissions}`** there."
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
