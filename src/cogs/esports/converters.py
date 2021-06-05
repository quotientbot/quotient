from models import *
from utils import QuoMember
from discord.ext import commands
from discord.ext.commands import Converter, BadArgument
import tortoise.exceptions


class ScrimConverter(Converter, Scrim):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await Scrim.get(pk=argument, guild_id=ctx.guild.id)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise BadArgument(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")


class TourneyConverter(Converter, Tourney):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await Tourney.get(pk=argument, guild_id=ctx.guild.id)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise BadArgument(f"This is not a valid Tourney ID.\n\nGet a valid ID with `{ctx.prefix}tourney config`")


class EasyMemberConverter(Converter):
    async def convert(self, ctx, argument: str):
        try:
            member = await QuoMember().convert(ctx, argument)
            return getattr(member, "mention")
        except commands.MemberNotFound:
            return "Invalid Member!"
