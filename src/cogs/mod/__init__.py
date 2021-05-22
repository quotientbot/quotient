from .utils import _self_clean_system, _complex_cleanup_strategy, do_removal
from core import Cog, Quotient, Context
from discord.ext import commands
from .events import *
from utils import checks
import typing
import discord
import re


class Mod(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    @checks.is_mod()
    @commands.cooldown(5, 1, type=commands.BucketType.user)
    async def selfclean(self, ctx: Context, search=100):
        """
        Clean Quotient's messages,
        Note: If bot has `manage_messages` permissions then it will delete the command messages too.
        """
        strategy = _self_clean_system
        if ctx.me.permissions_in(ctx.channel).manage_messages:
            strategy = _complex_cleanup_strategy

        search = min(max(2, search), 1000)

        spammers = await strategy(ctx, search)
        deleted = sum(spammers.values())
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append("")
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f"- **{author}**: {count}" for author, count in spammers)

        await ctx.send("\n".join(messages), delete_after=10)

    @commands.group(invoke_without_command=True, aliases=["purge"])
    @checks.has_permissions(manage_messages=True)
    async def clear(self, ctx, Choice: typing.Union[discord.Member, int], Amount: int = None):
        """
        An all in one purge command.
        Choice can be a Member or a number
        """
        if isinstance(Choice, discord.Member):
            search = Amount or 5
            return await do_removal(ctx, search, lambda e: e.author == Choice)

        try:
            search = int(Choice)
            await do_removal(ctx, search, lambda e: True)
        except:
            return await ctx.error("Only Integers are allowed.")

    @clear.command()
    @checks.has_permissions(manage_messages=True)
    async def embeds(self, ctx, search=100):
        """Removes messages that have embeds in them."""
        await do_removal(ctx, search, lambda e: len(e.embeds))

    @clear.command()
    @checks.has_permissions(manage_messages=True)
    async def files(self, ctx, search=100):
        """Removes messages that have attachments in them."""
        await do_removal(ctx, search, lambda e: len(e.attachments))

    @clear.command()
    @checks.has_permissions(manage_messages=True)
    async def images(self, ctx, search=100):
        """Removes messages that have embeds or attachments."""
        await do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @clear.command(name="all")
    @checks.has_permissions(manage_messages=True)
    async def _remove_all(self, ctx, search=100):
        """Removes all messages."""
        await do_removal(ctx, search, lambda e: True)

    @clear.command()
    @checks.has_permissions(manage_messages=True)
    async def user(self, ctx, member: discord.Member, search=100):
        """Removes all messages by the member."""
        await do_removal(ctx, search, lambda e: e.author == member)

    @clear.command()
    @checks.has_permissions(manage_messages=True)
    async def contains(self, ctx, *, substr: str):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.error("The substring length must be at least 3 characters.")
        else:
            await do_removal(ctx, 100, lambda e: substr in e.content)

    @clear.command(name="bot", aliases=["bots"])
    @checks.has_permissions(manage_messages=True)
    async def _bot(self, ctx, prefix=None, search=100):
        """Removes a bot user's messages and messages with their optional prefix."""

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))

        await do_removal(ctx, search, predicate)

    @clear.command(name="emoji", aliases=["emojis"])
    @checks.has_permissions(manage_messages=True)
    async def _emoji(self, ctx, search=100):
        """Removes all messages containing custom emoji."""
        custom_emoji = re.compile(r"<a?:[a-zA-Z0-9\_]+:([0-9]+)>")

        def predicate(m):
            return custom_emoji.search(m.content)

        await do_removal(ctx, search, predicate)

    @clear.command(name="reactions")
    @checks.has_permissions(manage_messages=True)
    async def _reactions(self, ctx, search=100):
        """Removes all reactions from messages that have them."""

        if search > 2000:
            return await ctx.send(f"Too many messages to search for ({search}/2000)")

        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()

        await ctx.send_m(f"Successfully removed {total_reactions} reactions.")


def setup(bot):
    bot.add_cog(Mod(bot))
    bot.add_cog(ModEvents(bot))
