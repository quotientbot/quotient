from discord.ext import commands
from PIL import ImageColor
import discord, re
import contextlib

from .exceptions import InvalidColor
from typing import Optional

__all__ = (
    "ColorConverter",
    "BannedMember",
    "ActionReason",
    "MemberID",
    "QuoRoleConverter",
    "QuoMemberConverter",
    "QuoUserConverter",
)


class ColorConverter(commands.Converter):
    async def convert(self, ctx, arg: str):
        with contextlib.suppress(AttributeError):
            match = re.match(r"\(?(\d+),?\s*(\d+),?\s*(\d+)\)?", arg)
            check = all(0 <= int(x) <= 255 for x in match.groups())

        if match and check:
            return discord.Color.from_rgb([int(i) for i in match.groups()])

        converter = commands.ColorConverter()
        try:
            result = await converter.convert(ctx, arg)
        except commands.BadColourArgument:
            try:
                color = ImageColor.getrgb(arg)
                result = discord.Color.from_rgb(*color)
            except ValueError:
                result = None

        if result:
            return result

        raise InvalidColor(arg)


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
            m = await commands.MemberConverter().convert(ctx, argument)
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


class QuoRoleConverter(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[discord.Role]:
        """
        Return Role, this works without taking case sensitivity into account.

        Raises commands.RoleNotFound if cannot find the role.
        """
        try:
            return await commands.RoleConverter().convert(ctx, argument)
        except commands.RoleNotFound:

            def check(role):
                return (
                    role.name.lower() == argument.lower()
                    or str(role).lower() == argument.lower()
                    or str(role.id) == argument
                )

            if found := discord.utils.find(check, ctx.guild.roles):
                return found

            raise commands.RoleNotFound(argument)


class QuoMemberConverter(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[discord.Member]:
        """
        Returns Member , it is better that commands.MemberConverter() because it finds member without
        taking case sensitivity into account.

        Raises commands.MemberNotFound
        """
        try:
            return await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:

            def check(member):
                return (
                    member.name.lower() == argument.lower()
                    or member.display_name.lower() == argument.lower()
                    or str(member).lower() == argument.lower()
                    or str(member.id) == argument
                )

            if found := discord.utils.find(check, ctx.guild.members):
                return found

            raise commands.MemberNotFound(argument)


class QuoUserConverter(commands.Converter):
    async def convert(self, ctx, argument):
        """
        This will return Member if member exists in the guild else will returns User.
        Raises commands.UserNotFound
        """
        if ctx.guild:
            try:
                return await QuoMemberConverter().convert(ctx, argument)

            except commands.MemberNotFound:
                pass

        try:
            return await commands.UserConverter().convert(ctx, argument)
        except:

            def check(user):
                return (
                    user.name.lower() == argument.lower()
                    or str(user).lower() == argument.lower()
                    or str(user.id) == argument
                )

            if found := discord.utils.find(check, ctx.bot.users):
                return found
            raise commands.UserNotFound(argument)
