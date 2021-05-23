from core import Cog, Quotient, Context
from discord.ext import commands
from models import User, Redeem , Guild
from prettytable import PrettyTable
from utils import checks, strtime
import secrets
import discord


class Premium(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def create_valid_redeem(self) -> str:
        while True:
            code = "QR_" + str(secrets.token_urlsafe(5).replace("_", "").replace("-", ""))

            check = await Redeem.filter(code=code)
            if not len(check):
                break

        return code

    @commands.command()
    @checks.is_premium_user()
    async def getredeem(self, ctx: Context):
        """Generate a new redeem code. You can use "boost" command if you want to directly upgrade a server."""
        record = await User.get_or_none(user_id=ctx.author.id)
        if not record.premiums:
            return await ctx.error(
                f"You have redeemed all your boosts, use `{ctx.prefix}mycodes` to check if you have any unused codes."
            )

        code = await self.create_valid_redeem()

        await Redeem.create(user_id=ctx.author.id, code=code, expire_time=record.premium_expire_time)
        await User.filter(user_id=ctx.author.id).update(premiums=record.premiums - 1)

        try:
            embed = discord.Embed(
                color=ctx.bot.color,
                description=f"Here's your Secret redeem code: \n||{code}||\nThis is powerful enough to upgrade a server to Quotient Premium.\n\nUse `{ctx.prefix}redeem <Your Code>` in the server which you want to upgrade.",
            )
            await ctx.author.send(embed=embed)
            await ctx.success("You 've a got a mail containing Quotient premium redeem code.")
        except:
            await ctx.success(
                f"I have generated a Quotient premium redeem code for you but unfortunately I couldn't send that to your DMs.\n\nKindly enable your DMs and use `{ctx.prefix}mycodes` to get them all."
            )

    @commands.command()
    @checks.is_premium_user()
    async def mycodes(self, ctx: Context):
        """Get all the redeem codes you have."""

        records = await Redeem.filter(user_id=ctx.author.id).order_by("-is_used")

        x = PrettyTable()
        x.field_names = ["Number", "Code", "Expiry", "Used"]
        for idx, i in enumerate(records, start=1):
            x.add_row([idx, i.code, strtime(i.expire_time), "Yes" if i.is_used is True else "No"])

        embed = discord.Embed(color=ctx.bot.color, description=f"```ml\n{x}```")
        embed.set_footer(text=f"To upgrade use: `{ctx.prefix}redeem <code>`")
        try:
            await ctx.author.send(embed=embed)
            await ctx.success("You 've a got a mail containing Quotient premium redeem codes.")
        except:
            await ctx.error("Kindly enable your DMs, I am unable to send you codes.")

    @commands.command()
    async def redeem(self, ctx: Context, redeemcode: str):
        pass

    @commands.command()
    async def boost(self, ctx: Context):
        pass

    @commands.command()
    async def myorders(self, ctx: Context):
        pass

    @commands.command()
    async def pstatus(self, ctx: Context):
        """Get your Quotient Premium status and the current server's."""
        user = await User.get_or_none(user_id=ctx.author.id)
        redeems = await Redeem.filter(user_id =ctx.author.id) #manytomany soon :c
        guild = await Guild.filter(guild_id =ctx.guild.id)

        atext = ""
        if not user.is_premium:
            atext = "\n> Activated: No!"
        

    @commands.command()
    async def perks(self, ctx: Context):
        """Get a list of all available perks you get when You purchase quotient premium."""
        await ctx.send("")


def setup(bot) -> None:
    bot.add_cog(Premium(bot))
