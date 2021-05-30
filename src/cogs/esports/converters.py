from discord.ext import commands
from typing import Optional
from models import *


class ScrimID(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[Scrim]:
        if not argument.isdigit():
            raise commands.BadArgument(
                f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`"
            )

        scrim = await Scrim.get_or_none(pk=int(argument), guild_id=ctx.guild.id)
        if scrim is None:
            raise commands.BadArgument(
                f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`"
            )

        return scrim


class TourneyID(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[Tourney]:
        if not argument.isdigit():
            raise commands.BadArgument(
                (f"This is not a valid Tourney ID.\n\nGet a valid ID with `{ctx.prefix}tourney config`")
            )

        tourney = await Tourney.get_or_none(pk=int(argument), guild_id=ctx.guild.id)
        if tourney is None:
            raise commands.BadArgument(
                f"This is not a valid Tourney ID.\n\nGet a valid ID with `{ctx.prefix}tourney config`"
            )

        return tourney
