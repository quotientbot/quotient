from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import os

import discord
from core import Context
from discord.ext import commands
from models import Guild


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


async def setup(bot: Quotient):
    await bot.add_cog(Premium(bot))
