from __future__ import annotations

import asyncio
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from datetime import datetime, timedelta

import config
import discord
from constants import random_greeting, random_thanks
from core import Cog, Context
from discord.ext import commands, tasks
from models import Guild, Timer, User, PremiumTxn
from tortoise.query_utils import Q
from utils import IST, strtime, emote, discord_timestamp

from .expire import (
    deactivate_premium,
    extra_guild_perks,
    remind_guild_to_pay,
    remind_user_to_pay,
)
from .views import PremiumView, PremiumPurchaseBtn


class PremiumCog(Cog, name="Premium"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.remind_peeps_to_pay.start()
        self.hook = discord.Webhook.from_url(self.bot.config.PUBLIC_LOG, session=self.bot.session)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pstatus(self, ctx: Context):
        """Get your Quotient Premium status and the current server's."""
        user = await User.get_or_none(user_id=ctx.author.id)
        guild = await Guild.filter(guild_id=ctx.guild.id).first()

        if not user.is_premium:
            atext = "\n> Activated: No!"

        else:
            atext = f"\n> Activated: Yes!\n> Ending: {discord_timestamp(user.premium_expire_time,'f')}"

        if not guild.is_premium:
            btext = "\n> Activated: No!"

        else:
            booster = guild.booster or await self.bot.fetch_user(guild.made_premium_by)
            btext = (
                f"\n> Activated: Yes!\n> Ending: {discord_timestamp(guild.premium_end_time,'f')}\n> Upgraded by: **{booster}**"
            )

        embed = self.bot.embed(ctx, title="Quotient Premium", url=f"{self.bot.config.WEBSITE}")
        embed.add_field(name="User", value=atext, inline=False)
        embed.add_field(name="Server", value=btext, inline=False)
        embed.set_thumbnail(url=ctx.guild.me.display_avatar.url)
        return await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=("perks", "pro"))
    async def premium(self, ctx: Context):
        """Checkout Quotient Premium Plans."""
        _e = discord.Embed(
            color=self.bot.color,
            description=f"[**Features of Quotient Pro -**]({self.bot.config.SERVER_LINK})\n\n"
            f"{emote.check} Access to `Quotient Pro` bot.\n"
            f"{emote.check} Unlimited Scrims.\n"
            f"{emote.check} Unlimited Tournaments.\n"
            f"{emote.check} Custom Reactions for Regs.\n"
            f"{emote.check} Smart SSverification.\n"
            f"{emote.check} Cancel-Claim Panel.\n"
            f"{emote.check} Premium Role + more...\n",
        )

        v = discord.ui.View(timeout=None)
        v.add_item(PremiumPurchaseBtn())
        await ctx.send(embed=_e, view=v)

    @tasks.loop(hours=48)
    async def remind_peeps_to_pay(self):
        await self.bot.wait_until_ready()

        await asyncio.sleep(900)
        async for user in User.filter(is_premium=True, premium_expire_time__lte=datetime.now(tz=IST) + timedelta(days=4)):
            _u = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user.pk)
            if _u:
                if not await self.ensure_reminders(user.pk, user.premium_expire_time):
                    await self.bot.reminders.create_timer(user.premium_expire_time, "user_premium", user_id=user.pk)

                await remind_user_to_pay(_u, user)

        async for guild in Guild.filter(is_premium=True, premium_end_time__lte=datetime.now(IST) + timedelta(days=4)):
            _g = self.bot.get_guild(guild.pk)

            if not await self.ensure_reminders(guild.pk, guild.premium_end_time):
                await self.bot.reminders.create_timer(guild.premium_end_time, "guild_premium", guild_id=guild.pk)

            if _g:
                await remind_guild_to_pay(_g, guild)

    async def ensure_reminders(self, _id: int, _time: datetime) -> bool:
        return await Timer.filter(
            Q(event="guild_premium", extra={"args": [], "kwargs": {"guild_id": _id}})
            | Q(event="user_premium", extra={"args": [], "kwargs": {"user_id": _id}}),
            expires=_time,
        ).exists()

    def cog_unload(self):
        self.remind_peeps_to_pay.stop()

    @Cog.listener()
    async def on_guild_premium_timer_complete(self, timer: Timer):
        guild_id = timer.kwargs["guild_id"]

        _g = await Guild.get_or_none(pk=guild_id)
        if not _g:
            return

        if not _g.premium_end_time == timer.expires:
            return

        _perks = "\n".join(await extra_guild_perks(guild_id))

        await deactivate_premium(guild_id)

        if (_ch := _g.private_ch) and _ch.permissions_for(_ch.guild.me).embed_links:

            _e = discord.Embed(
                color=discord.Color.red(), title="⚠️__**Quotient Pro Subscription Ended**__⚠️", url=config.SERVER_LINK
            )
            _e.description = (
                "This is to inform you that your subscription of Quotient Pro has been ended.\n\n"
                "*Following is a list of perks or data you lost:*"
            )

            _e.description += f"```diff\n{_perks}```"

            _roles = [
                role.mention
                for role in _ch.guild.roles
                if all((role.permissions.administrator, not role.managed, role.members))
            ]

            _view = PremiumView()
            await _ch.send(
                embed=_e,
                view=_view,
                content=", ".join(_roles[:2]) if _roles else _ch.guild.owner.mention,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )

    @Cog.listener()
    async def on_user_premium_timer_complete(self, timer: Timer):
        user_id = timer.kwargs["user_id"]
        _user = await User.get(pk=user_id)

        if not _user.premium_expire_time == timer.expires:
            return

        _q = "UPDATE user_data SET is_premium = FALSE ,premiums=0 ,made_premium = '{}' WHERE user_id = $1"
        await self.bot.db.execute(_q, user_id)

        member = await self.bot.get_or_fetch_member(self.bot.server, _user.pk)
        if member:
            await member.remove_roles(discord.Object(id=config.PREMIUM_ROLE))

    @Cog.listener()
    async def on_premium_purchase(self, txnId: str):
        record = await PremiumTxn.get(txnid=txnId)

        member = self.bot.server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE), reason="They purchased premium.")

        else:
            member = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, record.user_id)

        with suppress(discord.HTTPException, AttributeError):
            _e = discord.Embed(
                color=discord.Color.gold(), description=f"Thanks **{member}** for purchasing Quotient Premium."
            )
            _e.set_image(url=random_thanks())
            await self.hook.send(embed=_e, username="premium-logs", avatar_url=self.bot.config.PREMIUM_AVATAR)

        upgraded_guild = self.bot.get_guild(record.guild_id)
        _guild = await Guild.get_or_none(pk=record.guild_id)

        _e = discord.Embed(
            color=self.bot.color,
            title="Quotient Pro Purchase Successful!",
            url=self.bot.config.SERVER_LINK,
            description=(
                f"{random_greeting()} {member.mention},\n"
                f"Thanks for purchasing Quotient Premium. Your server **{upgraded_guild}** has access to Quotient Pro features until `{_guild.premium_end_time.strftime('%d-%b-%Y %I:%M %p')}`.\n\n"
                "[Click me to Invite Quotient Pro Bot to your server](https://discord.com/oauth2/authorize?client_id=902856923311919104&scope=applications.commands%20bot&permissions=21175985838)\n"
            ),
        )

        if member not in self.bot.server.members:
            _e.description += f"\n\n[To claim your Premium Role, Join Quotient HQ]({self.bot.config.SERVER_LINK})."

        _view = discord.ui.View(timeout=None)

        try:
            await member.send(embed=_e, view=_view)
        except discord.HTTPException:
            pass


async def setup(bot: Quotient) -> None:
    await bot.add_cog(PremiumCog(bot))
