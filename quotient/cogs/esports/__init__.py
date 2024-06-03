from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord import app_commands
from discord.ext import commands

from .slash import ScrimSlashCommands


class Esports(commands.Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot


async def setup(bot: Quotient) -> None:
    await bot.add_cog(Esports(bot))
    await bot.add_cog(ScrimSlashCommands(bot))
