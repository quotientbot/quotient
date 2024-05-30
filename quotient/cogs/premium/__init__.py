from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord.ext import commands
from lib import random_greeting_msg, random_thanks_image
from models import Guild, PremiumTxn

from .consts import get_pro_features_formatted
from .views import PremiumPurchaseBtn


class Premium(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def pstatus(self, ctx: Context):
        """Get current server's premium status."""
        guild = await Guild.get(pk=ctx.guild.id)

        embed = discord.Embed(color=self.bot.color)
        embed.add_field(
            name="Quotient Premium Status",
            value="Activated" if guild.is_premium else "Not Activated",
            inline=False,
        )

        if guild.is_premium:
            embed.add_field(
                name="- Expires At",
                value=discord.utils.format_dt(guild.premium_end_time, "f"),
                inline=False,
            )

            embed.add_field(
                name="- Activated By",
                value=await self.bot.get_or_fetch_member(
                    ctx.guild, guild.made_premium_by
                ),
                inline=False,
            )

        embed.set_thumbnail(url=ctx.guild.me.display_avatar.url)
        return await ctx.reply(embed=embed)

    @commands.hybrid_command(aliases=("perks", "pro"))
    async def premium(self, ctx: Context):
        """Checkout Quotient Premium Plans."""

        g = await Guild.get(pk=ctx.guild.id)

        _e = discord.Embed(
            color=self.bot.color,
            description=f"[**Features of Quotient Pro -**]({self.bot.config("SUPPORT_SERVER_LINK")})\n\n{get_pro_features_formatted()}",
        )

        v = discord.ui.View(timeout=None)
        v.add_item(
            PremiumPurchaseBtn(
                label=(
                    "Get Quotient Pro"
                    if not g.is_premium
                    else "Extend / Renew Quotient Pro"
                )
            )
        )
        await ctx.send(embed=_e, view=v)


    @commands.Cog.listener()
    async def on_premium_purchase(self, txnId: str):
        record = await PremiumTxn.get(txnid=txnId)

        member = self.bot.support_server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config('PREMIUM_ROLE_ID')), reason="They purchased premium.")

        else:
            member = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, record.user_id)


        _e = discord.Embed(
            color=discord.Color.gold(), description=f"Thanks **{member}** for purchasing Quotient Premium."
        )
        _e.set_image(url=random_thanks_image())
        await self.hook.send(embed=_e, username="premium-logs", avatar_url=self.bot.config('PRO_BOT_AVATAR_URL'))

        upgraded_guild = self.bot.get_guild(record.guild_id)
        _guild = await Guild.get_or_none(pk=record.guild_id)

        _e = discord.Embed(
            color=self.bot.color,
            title="Quotient Pro Purchase Successful!",
            url=self.bot.config('SUPPORT_SERVER_LINK'),
            description=(
                f"{random_greeting_msg()} {member.mention},\n"
                f"Thanks for purchasing Quotient Premium. Your server **__{upgraded_guild}__** "
                f"has access to Quotient Pro features until `{_guild.premium_end_time.strftime('%d-%b-%Y %I:%M %p')} IST`.\n\n"
            ),
        )


        v = discord.ui.View(timeout=None)
        v.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Join Support Server", url=self.bot.config('SUPPORT_SERVER_LINK'))
        )
        v.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Invite Quotient Pro", url=self.bot.config('PRO_INVITE_LINK'))
        )

        try:
            await member.send(embed=_e, view=v)
        except discord.HTTPException:
            pass

async def setup(bot: Quotient):
    await bot.add_cog(Premium(bot))
