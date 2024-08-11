from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Callable, List, Literal, Optional

if TYPE_CHECKING:
    from core import Quotient

import asyncio
import random
import re
from collections import Counter

import discord
from core import Context
from discord import app_commands
from discord.ext import commands

from quotient.cogs.mod.checks import role_permissions_check
from quotient.lib import CROSS, LOADING, Snowflake, user_input


class PurgeFlags(commands.FlagConverter):  # Src: R. Danny
    user: Optional[discord.User] = commands.flag(description="Remove messages from this user", default=None)
    contains: Optional[str] = commands.flag(description="Remove messages that contains this string (case sensitive)", default=None)
    prefix: Optional[str] = commands.flag(description="Remove messages that start with this string (case sensitive)", default=None)
    suffix: Optional[str] = commands.flag(description="Remove messages that end with this string (case sensitive)", default=None)
    after: Annotated[Optional[int], Snowflake] = commands.flag(
        description="Search for messages that come after this message ID", default=None
    )
    before: Annotated[Optional[int], Snowflake] = commands.flag(
        description="Search for messages that come before this message ID", default=None
    )
    bot: bool = commands.flag(description="Remove messages from bots (not webhooks!)", default=False)
    webhooks: bool = commands.flag(description="Remove messages from webhooks", default=False)
    embeds: bool = commands.flag(description="Remove messages that have embeds", default=False)
    files: bool = commands.flag(description="Remove messages that have attachments", default=False)
    emoji: bool = commands.flag(description="Remove messages that have custom emoji", default=False)
    reactions: bool = commands.flag(description="Remove messages that have reactions", default=False)
    require: Literal["any", "all"] = commands.flag(
        description='Whether any or all of the flags should be met before deleting messages. Defaults to "all"',
        default="all",
    )


class ModerationCmds(commands.Cog, name="Moderation"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def lock(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Lock a channel, removes send messages permission.
        """
        channel = channel or ctx.channel

        if not channel.permissions_for(ctx.author).manage_permissions:
            return await ctx.reply(embed=self.bot.error_embed(f"You don't have permissions to change settings of {channel.mention}."))

        if not channel.permissions_for(ctx.guild.me).manage_permissions:
            return await ctx.reply(embed=self.bot.error_embed(f"I don't have permissions to change settings of {channel.mention}."))

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = False
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"Locked by {ctx.author}")
        except discord.HTTPException as e:
            return await ctx.reply(embed=self.bot.error_embed(f"An error occurred while locking the channel: {e}"))

        await ctx.reply(embed=self.bot.success_embed(f"{channel.mention} has been locked."))

    @commands.hybrid_command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    async def unlock(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Unlock a channel, adds send messages permission to @everyone.
        """
        channel = channel or ctx.channel

        if not channel.permissions_for(ctx.author).manage_permissions:
            return await ctx.reply(embed=self.bot.error_embed(f"You don't have permissions to change settings of {channel.mention}."))

        if not channel.permissions_for(ctx.guild.me).manage_permissions:
            return await ctx.reply(embed=self.bot.error_embed(f"I don't have permissions to change settings of {channel.mention}."))

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = True
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"Unlocked by {ctx.author}")
        except discord.HTTPException as e:
            return await ctx.reply(embed=self.bot.error_embed(f"An error occurred while unlocking the channel: {e}"))

        await ctx.reply(embed=self.bot.success_embed(f"{channel.mention} has been unlocked."))

    @commands.hybrid_command(aliases=["purge"], usage="[search] [flags...]")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(search="How many messages to search for")
    async def clear(self, ctx: Context, search: int, *, flags: PurgeFlags):
        """Removes messages that meet a criteria.

        This command uses a syntax similar to Discord's search bar.
        The messages are only deleted if all options are met unless
        the `require:` flag is passed to override the behaviour.

        The following flags are valid.

        `user:` Remove messages from the given user.
        `contains:` Remove messages that contain a substring.
        `prefix:` Remove messages that start with a string.
        `suffix:` Remove messages that end with a string.
        `after:` Search for messages that come after this message ID.
        `before:` Search for messages that come before this message ID.
        `bot: yes` Remove messages from bots (not webhooks!)
        `webhooks: yes` Remove messages from webhooks
        `embeds: yes` Remove messages that have embeds
        `files: yes` Remove messages that have attachments
        `emoji: yes` Remove messages that have custom emoji
        `reactions: yes` Remove messages that have reactions
        `require: any or all` Whether any or all flags should be met before deleting messages.

        In order to use this command, you must have Manage Messages permissions.
        Note that the bot needs Manage Messages as well. These commands cannot
        be used in a private message.

        When the command is done doing its work, you will get a message
        detailing which users got removed and how many messages got removed.
        """
        await ctx.defer()

        predicates: list[Callable[[discord.Message], Any]] = []
        if flags.bot:
            if flags.webhooks:
                predicates.append(lambda m: m.author.bot)
            else:
                predicates.append(lambda m: (m.webhook_id is None or m.interaction is not None) and m.author.bot)
        elif flags.webhooks:
            predicates.append(lambda m: m.webhook_id is not None)

        if flags.embeds:
            predicates.append(lambda m: len(m.embeds))

        if flags.files:
            predicates.append(lambda m: len(m.attachments))

        if flags.reactions:
            predicates.append(lambda m: len(m.reactions))

        if flags.emoji:
            custom_emoji = re.compile(r"<a?:(\w+):(\d+)>")
            predicates.append(lambda m: custom_emoji.search(m.content))

        if flags.user:
            predicates.append(lambda m: m.author == flags.user)

        if flags.contains:
            predicates.append(lambda m: flags.contains in m.content)  # type: ignore

        if flags.prefix:
            predicates.append(lambda m: m.content.startswith(flags.prefix))  # type: ignore

        if flags.suffix:
            predicates.append(lambda m: m.content.endswith(flags.suffix))  # type: ignore

        if not predicates:
            # If nothing is passed then default to `True` to emulate ?purge all behaviour
            predicates.append(lambda m: True)

        op = all if flags.require == "all" else any

        def predicate(m: discord.Message) -> bool:
            r = op(p(m) for p in predicates)
            return r

        before = discord.Object(id=flags.before) if flags.before else None
        after = discord.Object(id=flags.after) if flags.after else None

        if before is None and ctx.interaction is not None:
            # If no before: is passed and we're in a slash command,
            # the deferred message will be deleted by purge and the followup will not show up.
            # To work around this, we need to get the deferred message's ID and avoid deleting it.
            before = await ctx.interaction.original_response()

        try:
            deleted = await ctx.channel.purge(limit=search, before=before, after=after, check=predicate)
        except discord.Forbidden as e:
            return await ctx.send(embed=self.bot.error_embed("I do not have permissions to delete messages."))
        except discord.HTTPException as e:
            return await ctx.send(embed=self.bot.error_embed(f"Error: {e} (try a smaller search?)"))

        spammers = Counter(m.author.display_name for m in deleted)
        deleted = len(deleted)
        messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
        if deleted:
            messages.append("")
            spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
            messages.extend(f"**{name}**: {count}" for name, count in spammers)

        to_send = "\n".join(messages)

        if len(to_send) > 2000:
            await ctx.send(embed=self.bot.success_embed(f"Successfully removed {deleted} messages."), delete_after=6)
        else:
            await ctx.send(to_send, delete_after=6)

    @commands.hybrid_command(name="role")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_permissions_check()
    @app_commands.rename(add_more_people="add-more-people")
    @app_commands.describe(
        role="The role to give", member="The member to give the role to", add_more_people="Whether to give the role to more people"
    )
    async def give_role(self, ctx: Context, role: discord.Role, *, member: discord.Member, add_more_people: bool = False):
        """
        Give a role to one or multiple members.
        """
        await ctx.defer()

        members = [member]
        if add_more_people:
            new_members = await user_input(
                ctx.interaction, f"Please select the members you want to give {role.mention}, apart from {member.mention}."
            )
            if new_members is None:
                return

            members.extend(new_members)

        members_length = len(members)

        if members_length == 1:
            try:
                await member.add_roles(role, reason=f"Role given by {ctx.author}")
            except discord.HTTPException as e:
                return await ctx.reply(embed=self.bot.error_embed(f"An error occurred while giving the role: {e}"))
            else:
                return await ctx.reply(embed=self.bot.success_embed(f"{role.mention} has been given to {member.mention}."))

        m = await ctx.reply(
            embed=discord.Embed(color=self.bot.color, description=f"Adding {role.mention} to {members_length} members... {LOADING}")
        )

        failed = []
        for member in members:
            try:
                await member.add_roles(role, reason=f"Role given by {ctx.author}")
            except discord.HTTPException as e:
                failed.append((member, e))
            else:
                await asyncio.sleep(random.uniform(0.5, 1.0))

        e = discord.Embed(color=self.bot.color, title="Role Assign Complete!")
        e.description = f"Added {role.mention} to `{members_length - len(failed)}/{members_length} members`.\n\n"
        if failed:
            e.description += "\n".join(f"{CROSS} **{member}**: {error}" for member, error in failed)

        try:
            await m.edit(embed=e)
        except discord.NotFound:
            await ctx.reply(embed=e)

    @commands.hybrid_command(name="rrole")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @role_permissions_check()
    @app_commands.rename(add_more_people="add-more-people")
    @app_commands.describe(
        role="The role to remove",
        member="The member to remove the role from",
        add_more_people="Whether to remove the role from more people",
    )
    async def remove_role(self, ctx: Context, role: discord.Role, member: discord.Member, add_more_people: bool = False):
        """
        Remove a role from one or multiple members.
        """
        await ctx.defer()

        members = [member]
        if add_more_people:
            new_members = await user_input(
                ctx.interaction, f"Please select the members you want to remove {role.mention} from, apart from {member.mention}."
            )
            if new_members is None:
                return

            members.extend(new_members)

        members_length = len(members)

        if members_length == 1:
            try:
                await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
            except discord.HTTPException as e:
                return await ctx.reply(embed=self.bot.error_embed(f"An error occurred while removing the role: {e}"))
            else:
                return await ctx.reply(embed=self.bot.success_embed(f"{role.mention} has been removed from {member.mention}."))

        m = await ctx.reply(
            embed=discord.Embed(
                color=self.bot.color, description=f"Removing {role.mention} from {members_length} members... {LOADING}"
            )
        )

        failed = []
        for member in members:
            try:
                await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
            except discord.HTTPException as e:
                failed.append((member, e))
            else:
                await asyncio.sleep(random.uniform(0.5, 1.0))

        e = discord.Embed(color=self.bot.color, title="Role Removal Complete!")
        e.description = f"Removed {role.mention} from `{members_length - len(failed)}/{members_length} members`.\n\n"
        if failed:
            e.description += "\n".join(f"{CROSS} **{member}**: {error}" for member, error in failed)

        try:
            await m.edit(embed=e)
        except discord.NotFound:
            await ctx.reply(embed=e)


async def setup(bot: Quotient):
    await bot.add_cog(ModerationCmds(bot))
