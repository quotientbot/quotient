from discord.ext import commands
from typing import Optional

import tortoise.exceptions
from models import *


class ScrimID(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[Scrim]:
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await Scrim.get(pk=argument)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise commands.BadArgument(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")


class TourneyID(commands.Converter):
    async def convert(self, ctx, argument) -> Optional[Tourney]:
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await Tourney.get(pk=argument)
            except tortoise.exceptions.DoesNotExist:
                pass

        raise commands.BadArgument(f"This is not a valid Tourney ID.\n\nGet a valid ID with `{ctx.prefix}tourney config`")
