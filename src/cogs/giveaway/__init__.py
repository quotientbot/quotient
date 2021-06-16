from core import Cog, Context, Quotient
from discord.ext import commands
from .gevents import Gevents
from models import Giveaway
import utils


class Giveaways(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    async def gcreate(self, ctx: Context):
        count = await Giveaway.filter(guild_id = ctx.guild.id , ended_at__not_isnull=True).count()
        if count >= 5 and not await ctx.is_premium():
            return await ctx.error(
                "You cannot host more than 5 giveaways concurrently on free tier.\n"
                "However, Quotient Premium allows you to host unlimited giveaways.\n\n"
                f"Checkout awesome Quotient Premium [here]({ctx.config.WEBSITE}/premium)"
                )
        
        
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
    bot.add_cog(Giveaways(bot))
    bot.add_cog(Gevents(bot))
