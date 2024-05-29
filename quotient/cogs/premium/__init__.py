from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import os

import discord
from core import Context
from discord.ext import commands
from models import Guild

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


async def setup(bot: Quotient):
    await bot.add_cog(Premium(bot))
