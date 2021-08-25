from models import *
from utils import QuoMember
from discord.ext import commands
from discord.ext.commands import Converter, BadArgument
import tortoise.exceptions


class MultiScrimConverter(Converter):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            if str(argument).lower() == "all":
                return await Scrim.filter(guild_id=ctx.guild.id).order_by("id")

        else:
            scrims = await Scrim.filter(pk=argument, guild_id=ctx.guild.id)
            if scrims:
                return scrims
        raise BadArgument("Kindly enter a valid Scrim ID or use **`all`** if you want denote all scrims.")


class EasyMemberConverter(Converter):
    async def convert(self, ctx, argument: str):
        try:
            member = await QuoMember().convert(ctx, argument)
            return getattr(member, "mention")
        except commands.MemberNotFound:
            return "Invalid Member!"


class PointsConverter(Converter):
    async def convert(self, ctx, argument: str):
        try:
            argument = int(argument)
        except:
            pass
        else:
            try:
                return await PointsInfo.get(pk=argument, guild_id=ctx.guild.id)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise BadArgument(f"This is not a valid Points ID.\n\nGet a valid ID with `{ctx.prefix}pt config`")
