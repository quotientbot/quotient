from core import Cog, Quotient, Context
from discord.ext import commands
import discord


class Utility(Cog, name="utility"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.group()
    async def autorole(self, ctx, off: str = None):
        if not off:
            return await ctx.send_help(ctx.command)

        ...

    @autorole.command(name="humans")
    async def autorole_humans(self, ctx: Context, *, role: discord.Role):
        pass

    @autorole.command(name="bots")
    async def autorole_bots(self, ctx: Context, *, role: discord.Role):
        pass

    @autorole.command(name="config")
    async def autorole_config(self, ctx: Context):
        pass


def setup(bot):
    bot.add_cog(Utility(bot))
