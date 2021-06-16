from core import Cog, Context, Quotient
from discord.ext import commands
from .gevents import Gevents
import utils


class Giveaway(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    async def gcreate(self, ctx: Context):
        pass

    @commands.command()
    async def gstart(self, ctx: Context):
        pass

    @commands.command()
    async def greroll(self, ctx: Context):
        pass

    @commands.command()
    async def gend(self, ctx: Context):
        pass

    @commands.command()
    async def glist(self, ctx: Context):
        pass

    @commands.command()
    async def gcancel(self, ctx: Context):
        pass

    @commands.command()
    async def gschedule(self, ctx: Context):
        pass


def setup(bot):
    bot.add_cog(Giveaway(bot))
    bot.add_cog(Gevents(bot))
