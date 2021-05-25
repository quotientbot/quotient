from utils.time import human_timedelta
from .utils import _self_clean_system, _complex_cleanup_strategy, do_removal, role_checker
from core import Cog, Quotient, Context
from models import Lockdown, ArrayAppend
from discord.ext import commands
from .events import *
from utils import ActionReason, MemberID, BannedMember, emote, FutureTime, LockType
from typing import Optional, Union
import discord
import re


class Mod(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command()
    @commands.has_permissions(manage_guild=True)
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
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, Choice: Union[discord.Member, int], Amount: int = None):
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
    @commands.has_permissions(manage_messages=True)
    async def embeds(self, ctx, search=100):
        """Removes messages that have embeds in them."""
        await do_removal(ctx, search, lambda e: len(e.embeds))

    @clear.command()
    @commands.has_permissions(manage_messages=True)
    async def files(self, ctx, search=100):
        """Removes messages that have attachments in them."""
        await do_removal(ctx, search, lambda e: len(e.attachments))

    @clear.command()
    @commands.has_permissions(manage_messages=True)
    async def images(self, ctx, search=100):
        """Removes messages that have embeds or attachments."""
        await do_removal(ctx, search, lambda e: len(e.embeds) or len(e.attachments))

    @clear.command(name="all")
    @commands.has_permissions(manage_messages=True)
    async def _remove_all(self, ctx, search=100):
        """Removes all messages."""
        await do_removal(ctx, search, lambda e: True)

    @clear.command()
    @commands.has_permissions(manage_messages=True)
    async def user(self, ctx, member: discord.Member, search=100):
        """Removes all messages by the member."""
        await do_removal(ctx, search, lambda e: e.author == member)

    @clear.command()
    @commands.has_permissions(manage_messages=True)
    async def contains(self, ctx, *, substr: str):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.error("The substring length must be at least 3 characters.")
        else:
            await do_removal(ctx, 100, lambda e: substr in e.content)

    @clear.command(name="bot", aliases=["bots"])
    @commands.has_permissions(manage_messages=True)
    async def _bot(self, ctx, prefix=None, search=100):
        """Removes a bot user's messages and messages with their optional prefix."""

        def predicate(m):
            return (m.webhook_id is None and m.author.bot) or (prefix and m.content.startswith(prefix))

        await do_removal(ctx, search, predicate)

    @clear.command(name="emoji", aliases=["emojis"])
    @commands.has_permissions(manage_messages=True)
    async def _emoji(self, ctx, search=100):
        """Removes all messages containing custom emoji."""
        custom_emoji = re.compile(r"<a?:[a-zA-Z0-9\_]+:([0-9]+)>")

        def predicate(m):
            return custom_emoji.search(m.content)

        await do_removal(ctx, search, predicate)

    @clear.command(name="reactions")
    @commands.has_permissions(manage_messages=True)
    async def _reactions(self, ctx, search=100):
        """Removes all reactions from messages that have them."""

        if search > 2000:
            return await ctx.send(f"Too many messages to search for ({search}/2000)")

        total_reactions = 0
        async for message in ctx.history(limit=search, before=ctx.message):
            if len(message.reactions):
                total_reactions += sum(r.count for r in message.reactions)
                await message.clear_reactions()

        await ctx.success(f"Successfully removed {total_reactions} reactions.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.cooldown(2, 1, type=commands.BucketType.user)
    async def kick(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Kicks a member from the server.
        In order for this to work, the bot must have Kick Member permissions.
        To use this command you must have Kick Members permission.
        """
        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.kick(member, reason=reason)
        await ctx.success(f"{str(member)} has been successfully kicked out!")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(2, 1, type=commands.BucketType.user)
    @commands.bot_has_guild_permissions(ban_members=True)
    async def ban(self, ctx, member: MemberID, *, reason: ActionReason = None):
        """Bans a member from the server.
        You can also ban from ID to ban regardless whether they're
        in the server or not.
        In order for this to work, the bot must have Ban Member permissions.
        To use this command you must have Ban Members permission.
        """

        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.ban(member, reason=reason)
        await ctx.success(f"{str(member)} has been successfully banned!")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.cooldown(2, 1, type=commands.BucketType.user)
    async def unban(self, ctx, member: BannedMember, *, reason: ActionReason = None):
        """Unbans a member from the server.
        You can pass either the ID of the banned member or the Name#Discrim
        combination of the member. Typically the ID is easiest to use.
        In order for this to work, the bot must have Ban Member permissions.
        To use this command you must have Ban Members permissions.
        """

        if reason is None:
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"

        await ctx.guild.unban(member.user, reason=reason)
        if member.reason:
            await ctx.send(f"Unbanned {member.user} (ID: {member.user.id}), previously banned for {member.reason}.")
        else:
            await ctx.success(f"Unbanned {member.user} (ID: {member.user.id}).")

    @commands.group(invoke_without_command=True, aliases=["addrole", "giverole"])
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role, members: commands.Greedy[discord.Member]):
        """
        Add a role to one or multiple users.
        """
        if await role_checker(ctx, role):
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
            failed = []
            for m in members:
                if not role in m.roles:
                    try:
                        await m.add_roles(role, reason=reason)
                    except:
                        failed.append(str(m))
                        continue

            if len(failed) > 0:
                return await ctx.error(f"Unfortunately, I couldn't add roles to:\n{', '.join(failed)}")
            else:
                await ctx.message.add_reaction(emote.check)

    @role.command(name="humans")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def role_humans(self, ctx, *, role: discord.Role):
        """Add a role to all human users."""
        if await role_checker(ctx, role):
            prompt = await ctx.prompt(
                title="Are you sure want to do this?",
                message=f"{role.mention} will be added to all human users in the server.",
            )
            if prompt:
                members = filter(lambda x: not x.bot and role not in x.roles, ctx.guild.members)
                await ctx.send(embed=ctx.embed.default(ctx, description=f"Adding role to {len(members)} humans..."))
                reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
                failed = 0
                for m in members:
                    try:
                        await m.add_roles(role, reason=reason)
                    except:
                        failed += 1
                        continue

                if failed > 0:
                    return await ctx.error(f"Unfortunately, I couldn't add roles to {failed} members.")

                else:
                    await ctx.send(f"{emote.check} | Successfully added role to {len(members)} members.")

    @role.command(name="bots")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def role_bots(self, ctx, *, role: discord.Role):
        if await role_checker(ctx, role):
            """Add a role to all bot users."""
            prompt = await ctx.prompt(
                title="Are you sure want to do this?", message=f"{role.mention} will be added to all bots in the server."
            )
            if prompt:
                members = filter(lambda x: x.bot and role not in x.roles, ctx.guild.members)
                await ctx.send(embed=ctx.embed.default(ctx, description=f"Adding role to {len(members)} bots..."))
                reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
                failed = 0
                for m in members:
                    try:
                        await m.add_roles(role, reason=reason)
                    except:
                        failed += 1
                        continue

                if failed > 0:
                    return await ctx.error(f"Unfortunately, I couldn't add roles to {failed} bots.")

                else:
                    await ctx.send(f"{emote.check} | Successfully added role to {len(members)} bots.")

    @role.command(name="all")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def role_all(self, ctx, *, role: discord.Role):
        """Add a role to everyone on the server"""
        if await role_checker(ctx, role):
            prompt = await ctx.prompt(
                title="Are you sure want to do this?", message=f"{role.mention} will be added to everyone in the server."
            )
            if prompt:
                members = filter(lambda x: role not in x.roles, ctx.guild.members)
                await ctx.send(embed=ctx.embed.default(ctx, description=f"Adding role to {len(members)} members..."))
                reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
                failed = 0
                for m in members:
                    try:
                        await m.add_roles(role, reason=reason)
                    except:
                        failed += 1
                        continue

                if failed > 0:
                    return await ctx.error(f"Unfortunately, I couldn't add roles to {failed} members.")

                else:
                    await ctx.send(f"{emote.check} | Successfully added role to {len(members)} members.")

    @commands.group(invoke_without_command=True, aliases=["removerole", "takerole"])
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def rrole(self, ctx, role: discord.Role, members: commands.Greedy[discord.Member]):
        """Remove a role from one or multiple users."""
        if await role_checker(ctx, role):
            reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
            failed = []
            for m in members:
                if role in m.roles:
                    try:
                        await m.remove_roles(role, reason=reason)
                    except:
                        failed.append(str(m))
                        continue

            if len(failed) > 0:
                return await ctx.error(f"Unfortunately, I couldn't remove roles from:\n{', '.join(failed)}")
            else:
                await ctx.message.add_reaction(emote.check)

    @rrole.command(name="humans")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def rrole_humans(self, ctx, *, role: discord.Role):
        """Remove a role from all human users."""
        if await role_checker(ctx, role):
            prompt = await ctx.prompt(
                title="Are you sure want to do this?",
                message=f"{role.mention} will be removed from all human users in the server.",
            )
            if prompt:
                members = filter(lambda x: not x.bot and role in x.roles, ctx.guild.members)
                await ctx.send(embed=ctx.embed.default(ctx, description=f"Removing role from {len(members)} humans..."))
                reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
                failed = 0
                for m in members:
                    try:
                        await m.remove_roles(role, reason=reason)
                    except:
                        failed += 1
                        continue

                if failed > 0:
                    return await ctx.error(f"Unfortunately, I couldn't remove roles from {failed} members.")

                else:
                    await ctx.send(f"{emote.check} | Successfully removed role from {len(members)} members.")

    @rrole.command(name="bots")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def rrole_bots(self, ctx, *, role: discord.Role):
        """Remove a role from all the bots."""
        if await role_checker(ctx, role):
            prompt = await ctx.prompt(
                title="Are you sure want to do this?",
                message=f"{role.mention} will be removed from all bot users in the server.",
            )
            if prompt:
                members = filter(lambda x: x.bot and role in x.roles, ctx.guild.members)
                await ctx.send(embed=ctx.embed.default(ctx, description=f"Removing role from {len(members)} bots..."))
                reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
                failed = 0
                for m in members:
                    try:
                        await m.remove_roles(role, reason=reason)
                    except:
                        failed += 1
                        continue

                if failed > 0:
                    return await ctx.error(f"Unfortunately, I couldn't remove roles from {failed} bots.")

                else:
                    await ctx.send(f"{emote.check} | Successfully removed role from {len(members)} bots.")

    @rrole.command(name="all")
    @commands.has_guild_permissions(manage_roles=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def rrole_all(self, ctx, *, role: discord.Role):
        """Remove a role from everyone on the server."""
        if await role_checker(ctx, role):
            prompt = await ctx.prompt(
                title="Are you sure want to do this?",
                message=f"{role.mention} will be removed from everyone in the server.",
            )
            if prompt:
                members = filter(lambda x: role in x.roles, ctx.guild.members)
                await ctx.send(embed=ctx.embed.default(ctx, description=f"Removing role from {len(members)} members..."))
                reason = f"Action done by {ctx.author} (ID: {ctx.author.id})"
                failed = 0
                for m in members:
                    try:
                        await m.remove_roles(role, reason=reason)
                    except:
                        failed += 1
                        continue

                if failed > 0:
                    return await ctx.error(f"Unfortunately, I couldn't remove roles from {failed} members.")

                else:
                    await ctx.send(f"{emote.check} | Successfully removed role from {len(members)} members.")

    @commands.group(invoke_without_command=True, aliases=("lockdown",))
    async def lock(self, ctx: Context, channel: Optional[discord.TextChannel], duration: Optional[FutureTime]):
        """Lock a channel , category or the whole server."""
        channel = channel or ctx.channel
        check = await Lockdown.filter(guild_id=ctx.guild.id, channel_id=channel.id, type=LockType.channel).first()

        if check != None:
            return await ctx.error(
                f"**{channel}** is already locked.\n\nTime Remaining: {human_timedelta(check.expire_time)}"
            )

        if not channel.permissions_for(ctx.me).manage_channels:
            return await ctx.error(f"I need `manage_channels` permission in **{channel}**")

        elif not channel.permissions_for(ctx.author).manage_channels:
            return await ctx.error(f"You need `manage channels` permission in **{channel}** to use this.")

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=perms)

        if duration is None:  # we don't want to store if duration is None.
            return await ctx.send_m(f"Locked down **{channel.name}**")

        await Lockdown.create(
            guild_id=ctx.guild.id,
            type=LockType.channel,
            expire_time=duration.dt,
            channel_id=channel.id,
            author_id=ctx.author.id,
        )
        timer = await self.bot.reminders.create_timer(
            duration.dt, "lockdown", _type=LockType.channel.value, channel_id=channel.id
        )
        await ctx.success(f"Locked down **{channel}** for {human_timedelta(duration.dt,source= timer.created)}")

    @lock.command()
    async def category(self, ctx, category: discord.CategoryChannel, duration: Optional[FutureTime]):
        check = await Lockdown.filter(guild_id=ctx.guild.id, type=LockType.category, channel_id=category.id)

        if check is not None:
            return await ctx.error(f"**{category}** is already locked.")


def setup(bot):
    bot.add_cog(Mod(bot))
    bot.add_cog(ModEvents(bot))
