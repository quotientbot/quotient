import asyncio
import contextlib
import re
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Optional

import discord
from discord.ext import commands
from PIL import ImageColor

__all__ = (
    "BannedMember",
    "ActionReason",
    "MemberID",
    "QuoRole",
    "QuoMember",
    "QuoUser",
    "QuoColor",
    "QuoCategory",
    "QuoTextChannel",
    "to_async",
)


class to_async:
    def __init__(self, *, executor: Optional[ThreadPoolExecutor] = None):
        self.executor = executor

    def __call__(self, blocking):
        @wraps(blocking)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            if not self.executor:
                self.executor = ThreadPoolExecutor()

            func = partial(blocking, *args, **kwargs)

            return await loop.run_in_executor(self.executor, func)

        return wrapper


class QuoColor:
    @classmethod
    async def convert(cls, ctx, arg):
        match, check = None, False
        with contextlib.suppress(AttributeError):
            match = re.match(r"\(?(\d+),?\s*(\d+),?\s*(\d+)\)?", arg)
            check = all(0 <= int(x) <= 255 for x in match.groups())

        if match and check:
            return discord.Color.from_rgb(*[int(i) for i in match.groups()])

        _converter = commands.ColorConverter()
        result = None

        try:
            result = await _converter.convert(ctx, arg)
        except commands.BadColorArgument:
            with contextlib.suppress(ValueError):
                color = ImageColor.getrgb(arg)
                result = discord.Color.from_rgb(*color)

        if result:
            return result

        return await ctx.error(f"`{arg}` isn't a valid color.", 4)


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument("This member has not been banned before.") from None

        ban_list = await ctx.guild.bans()
        entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument("This member has not been banned before.")
        return entity


class ActionReason(commands.Converter):
    async def convert(self, ctx, argument):
        ret = f"{ctx.author} (ID: {ctx.author.id}): {argument}"

        if len(ret) > 512:
            reason_max = 512 - len(ret) + len(argument)
            raise commands.BadArgument(f"Reason is too long ({len(argument)}/{reason_max})")
        return ret


def can_execute_action(ctx, user, target):
    return user.id == ctx.bot.owner_id or user == ctx.guild.owner or user.top_role > target.top_role


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await QuoMember().convert(ctx, argument)
        except commands.BadArgument:
            try:
                member_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
            else:
                m = await ctx.bot.get_or_fetch_member(ctx.guild, member_id)
                if m is None:
                    # hackban case
                    return type("_Hackban", (), {"id": member_id, "__str__": lambda s: f"Member ID {s.id}"})()

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument("You cannot do this action on this user due to role hierarchy.")

        elif not can_execute_action(ctx, ctx.me, m):
            raise commands.BadArgument("I cannot do this action on this user due to role hierarchy.")

        return m


class QuoRole(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[discord.Role]:
        """
        Return Role, this works without taking case sensitivity into account.

        Raises commands.RoleNotFound if cannot find the role.
        """
        try:
            return await commands.RoleConverter().convert(ctx, argument)
        except commands.RoleNotFound:

            def check(role):
                return role.name.lower() == argument.lower() or str(role).lower() == argument.lower()

            if found := discord.utils.find(check, ctx.guild.roles):
                return found

            raise commands.RoleNotFound(argument)


class QuoMember(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[discord.Member]:
        """
        Returns Member , it is better that commands.MemberConverter() because it finds member without
        taking case sensitivity into account.

        Raises commands.MemberNotFound
        """
        argument = argument.strip()
        try:
            return await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:

            def check(member):
                return (
                    member.name.lower() == argument.lower()
                    or member.display_name.lower() == argument.lower()
                    or str(member).lower() == argument.lower()
                )

            if found := discord.utils.find(check, ctx.guild.members):
                return found

            raise commands.MemberNotFound(argument)


class QuoUser(commands.Converter):
    async def convert(self, ctx, argument):
        """
        This will return Member if member exists in the guild else will returns User.
        Raises commands.UserNotFound
        """
        argument = argument.strip()
        if ctx.guild:
            try:
                return await QuoMember().convert(ctx, argument)

            except commands.MemberNotFound:
                pass

        try:
            return await commands.UserConverter().convert(ctx, argument)

        except commands.UserNotFound:

            def check(user):
                return (
                    user.name.lower() == argument.lower()
                    or str(user).lower() == argument.lower()
                    or user.id == str(argument)
                )

            if found := discord.utils.find(check, ctx.bot.users):
                return found
            raise commands.UserNotFound(argument)


class QuoCategory(commands.Converter):
    async def convert(self, ctx: commands.Context, argument):
        try:
            return await commands.CategoryChannelConverter().convert(ctx, argument)
        except commands.ChannelNotFound:

            def check(category):
                return category.name.lower() == argument.lower()

            if found := discord.utils.find(check, ctx.guild.categories):
                return found

            raise commands.ChannelNotFound(argument)


class QuoTextChannel(commands.Converter):
    async def convert(self, ctx: commands.Context, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.ChannelNotFound:

            def check(channel: discord.TextChannel):
                return channel.name.lower() == argument.lower()

            if found := discord.utils.find(check, ctx.guild.text_channels):
                return found

            raise commands.ChannelNotFound(argument)
