from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog, Context
from discord.ext import commands
from models import User, Redeem, Guild, ArrayAppend
from utils import checks, strtime, IST
from datetime import datetime, timedelta

from .views import InvitePrime
import discord
import config

from core import event_bot_check


class Premium(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.command()
    @checks.is_premium_user()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def boost(self, ctx: Context):
        """Upgrade your server with Quotient Premium."""

        def __use_prime_bot(g: discord.Guild) -> bool:
            return bool(g.get_member(config.PREMIUM_BOT))

        user = await User.get(user_id=ctx.author.id)
        if not user.premiums:
            return await ctx.error(
                "You have no Quotient Prime Boosts left.\n\nKindly purchase premium again to get 1 boost.\n"
            )

        guild = await Guild.get(guild_id=ctx.guild.id)

        if guild.premium_end_time and guild.premium_end_time > datetime.now(tz=IST):
            end_time = guild.premium_end_time + timedelta(days=30)

        else:
            end_time = datetime.now(tz=IST) + timedelta(days=30)

        prompt = await ctx.prompt(
            f"This server will be upgraded with Quotient Premium till {strtime(end_time)}."
            "\n\n*This action is irreversible.*",
            title="Are you sure you want to continue?",
        )
        if not prompt:
            return await ctx.simple(f"Alright, Aborting.")

        await user.refresh_from_db(("premiums",))
        if not user.premiums:
            return await ctx.send("don't be a dedh shana bruh")

        await guild.select_for_update().update(
            is_premium=True,
            made_premium_by=ctx.author.id,
            premium_end_time=end_time,
            embed_color=self.bot.config.PREMIUM_COLOR,
            bot_id=config.PREMIUM_BOT if __use_prime_bot(ctx.guild) else self.bot.user.id,
        )
        await user.select_for_update().update(
            premiums=user.premiums - 1, made_premium=ArrayAppend("made_premium", ctx.guild.id)
        )
        await self.bot.reminders.create_timer(end_time - timedelta(days=4), "guild_premium_reminder", guild=ctx.guild.id)
        await self.bot.reminders.create_timer(end_time, "guild_premium", guild_id=ctx.guild.id)

        await ctx.success(f"Congratulations, this server has been upgraded to Quotient Premium till {strtime(end_time)}.")

        if not __use_prime_bot(ctx.guild):
            _view = InvitePrime(ctx.guild.id)
            await ctx.send(embed=_view.embed_msg, view=_view)

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
            booster = ctx.guild.get_member(guild.made_premium_by) or await self.bot.fetch_user(guild.made_premium_by)
            btext = (
                f"\n> Activated: Yes!\n> Expiry Time: `{strtime(guild.premium_end_time)}`\n> Boosted by: **{booster}**"
            )

        embed = self.bot.embed(ctx, title="Quotient Premium", url=f"{self.bot.config.WEBSITE}")
        embed.add_field(name="User", value=atext, inline=False)
        embed.add_field(name="Server", value=btext, inline=False)
        return await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def perks(self, ctx: Context):
        """Get a list of all available perks you get when You purchase quotient premium."""
        return await ctx.premium_mango("*I love you, Buy Premium and I'll love you even more*\n*~ deadshot#7999*")

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if not self.bot.user.id == config.PREMIUM_BOT:
            return

        _g = await Guild.get_or_none(pk=guild.id)
        if not _g:
            return

        if not _g.is_premium:
            return await guild.leave()

        await _g.select_for_update().update(bot_id=self.bot.user.id, embed_color=config.PREMIUM_COLOR)
        await self.bot.cache.update_guild_cache(guild.id)

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        _g = await Guild.get_or_none(pk=guild.id, bot_id=config.PREMIUM_BOT)
        if not _g:
            return

        if self.bot.user.id == config.PREMIUM_BOT:
            await _g.select_for_update().update(bot_id=config.MAIN_BOT)

    @Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.id == config.MAIN_BOT:
            _g = await Guild.get_or_none(pk=member.guild.id, bot_id=config.PREMIUM_BOT)
            if _g:
                await self.bot.convey_important_message(member.guild, ("invite krlo vapis"))

    # @commands.command()
    # @commands.bot_has_permissions(embed_links=True)
    # async def changequo(self, ctx: Context):
    #     """Switch to another Quotient Premium bot."""

    #     if not await ctx.is_premium_guild():
    #         return await ctx.error("This server is not boosted. Please use `qboost`.")

    #     await self.bot.reminders.create_timer(
    #         datetime.now(tz=IST) + timedelta(minutes=1),
    #         "premium_activation",
    #         channel_id=ctx.channel.id,
    #         guild_id=ctx.guild.id,
    #     )

    #     await Guild.get(pk=ctx.guild.id).update(waiting_activation=True)

    #     _view = PremiumActivate(ctx.guild.id)
    #     await ctx.send(_view.initial_message, view=_view, file=await _view.image)

    # @Cog.listener()
    # async def on_premium_activation_timer_complete(self, timer: Timer):
    #     channel_id, guild_id = timer.kwargs["channel_id"], timer.kwargs["guild_id"]

    #     guild = await Guild.get(pk=guild_id)
    #     if not guild.is_premium or not guild.waiting_activation:
    #         return

    #     await guild.select_for_update().update(waiting_activation=False)

    #     channel = self.bot.get_channel(channel_id)
    #     await channel.send("Quotient Change request timed out. Kindly use `qchangequo` command again.")


def setup(bot) -> None:
    bot.add_cog(Premium(bot))
