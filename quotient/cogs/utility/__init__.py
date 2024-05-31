from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord.ext import commands
from models import AutoPurge, Guild

from .views import AutopurgeView


class Utility(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.hybrid_command(name="autopurge", aliases=["ap"])
    async def autopurge_cmd(self, ctx: Context):
        v = AutopurgeView(self.bot, ctx)
        v.message = await ctx.send(embed=await v.initial_msg(), view=v)


async def setup(bot: Quotient):
    await bot.add_cog(Utility(bot))
