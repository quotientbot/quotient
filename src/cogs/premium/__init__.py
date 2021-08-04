from core import Cog, Quotient, Context
from discord.ext import commands
from models import User, Redeem, Guild, ArrayAppend
from prettytable import PrettyTable
from utils import checks, strtime, IST
from datetime import datetime, timedelta
import constants
import secrets
import discord
import textwrap


class Premium(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @property
    def reminders(self):  # yes I do this a lot.
        return self.bot.get_cog("Reminders")

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
        code = await Redeem.get_or_none(code=redeemcode)
        if not code:
            return await ctx.send("That's an invalid code :c")

        elif code.is_used:
            return await ctx.send(f"You are late bud! Someone already redeemed it.")

        guild = await Guild.get(guild_id=ctx.guild.id)

        if guild.premium_end_time and guild.premium_end_time > datetime.now(tz=IST):
            end_time = guild.premium_end_time + timedelta(days=30)

        else:
            end_time = datetime.now(tz=IST) + timedelta(days=30)

        user = await User.get(user_id=code.user_id)
        prompt = await ctx.prompt(
            f"This server will be upgraded with Quotient Premium till {strtime(end_time)}.",
            title="Are you sure you want to continue?",
        )
        if prompt:
            await Guild.filter(guild_id=ctx.guild.id).update(
                is_premium=True, made_premium_by=code.user_id, premium_end_time=end_time
            )
            await self.reminders.create_timer(end_time - timedelta(days=4), "guild_premium_reminder", guild=ctx.guild.id)
            await self.reminders.create_timer(end_time, "guild_premium", guild_id=ctx.guild.id)
            await User.filter(user_id=code.user_id).update(
                premiums=user.premiums - 1, made_premium=ArrayAppend("made_premium", ctx.guild.id)
            )
            await Redeem.filter(code=redeemcode).update(is_used=True, used_at=datetime.now(tz=IST), used_by=ctx.author.id)

            await ctx.success(
                f"Congratulations, this server has been upgraded to Quotient Premium till {strtime(end_time)}."
            )
        else:
            await ctx.success(f"Alright")

    @commands.command()
    @checks.is_premium_user()
    async def boost(self, ctx: Context):
        """Upgrade your server with Quotient Premium."""
        user = await User.get(user_id=ctx.author.id)
        if not user.premiums:
            return await ctx.error(
                f"You have redeemed all your boosts, use `{ctx.prefix}mycodes` to check if you have any unused codes."
            )

        guild = await Guild.get(guild_id=ctx.guild.id)

        if guild.premium_end_time and guild.premium_end_time > datetime.now(tz=IST):
            end_time = guild.premium_end_time + timedelta(days=30)

        else:
            end_time = datetime.now(tz=IST) + timedelta(days=30)

        prompt = await ctx.prompt(
            f"This server will be upgraded with Quotient Premium till {strtime(end_time)}.",
            title="Are you sure you want to continue?",
        )
        if prompt:

            await user.refresh_from_db(("premiums",))
            if not user.premiums:
                return await ctx.send("don't be a dedh shana bruh")

            await Guild.filter(guild_id=ctx.guild.id).update(
                is_premium=True, made_premium_by=ctx.author.id, premium_end_time=end_time
            )
            await User.filter(user_id=ctx.author.id).update(
                premiums=user.premiums - 1, made_premium=ArrayAppend("made_premium", ctx.guild.id)
            )
            await self.reminders.create_timer(end_time - timedelta(days=4), "guild_premium_reminder", guild=ctx.guild.id)
            await self.reminders.create_timer(end_time, "guild_premium", guild_id=ctx.guild.id)

            await ctx.success(
                f"Congratulations, this server has been upgraded to Quotient Premium till {strtime(end_time)}."
            )
        else:
            await ctx.success(f"Alright")

    # @commands.command()
    # async def myorders(self, ctx: Context):
    #     laters baby

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pstatus(self, ctx: Context):
        """Get your Quotient Premium status and the current server's."""
        user = await User.get_or_none(user_id=ctx.author.id)
        redeems = await Redeem.filter(user_id=ctx.author.id)  # manytomany soon :c
        guild = await Guild.filter(guild_id=ctx.guild.id).first()

        if not user.is_premium:
            atext = "\n> Activated: No!"

        else:
            atext = f"\n> Activated: Yes!\n> Expiry: `{strtime(user.premium_expire_time)}`\n> Boosts Left: {user.premiums}\n> Boosted Servers: {len(set(user.made_premium))}\n> Redeem Codes: {len(redeems)}"

        if not guild.is_premium:
            btext = "\n> Activated: No!"

        else:
            booster = ctx.guild.get_member(guild.made_premium_by) or await self.bot.fetch_member(guild.made_premium_by)
            btext = (
                f"\n> Activated: Yes!\n> Expiry Time: `{strtime(guild.premium_end_time)}`\n> Boosted by: **{booster}**"
            )

        embed = self.bot.embed(ctx, title="Quotient Premium", url=f"{self.bot.config.WEBSITE}")
        embed.add_field(name="User", value=atext, inline=False)
        embed.add_field(name="Server", value=btext, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def perks(self, ctx: Context):
        """Get a list of all available perks you get when You purchase quotient premium."""
        table = PrettyTable()
        table.field_names = ["Perks", "Free Tier", "Premium Tier"]

        for key, val in constants.perks.items():
            a, b = val
            table.add_row([key, a, b])

        table = table.get_string()
        embed = self.bot.embed(ctx, title="Free-Premium Comparison", url=f"{self.bot.config.WEBSITE}/premium")
        embed.description = f"```{table}```"
        # embed.set_image(url="https://media.discordapp.net/attachments/851846932593770496/856601287566557184/unknown.png")
        await ctx.send(embed=embed)


def setup(bot) -> None:
    bot.add_cog(Premium(bot))
