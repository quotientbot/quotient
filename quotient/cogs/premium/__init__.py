from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord.ext import commands
from humanize import naturaldelta

from quotient.lib import INFO, TabularData, random_greeting_msg, random_thanks_image
from quotient.models import Guild, GuildTier, PremiumQueue, PremiumTxn

from .checks import *
from .views import *


class Premium(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.hybrid_command(aliases=("pro", "pstatus"))
    async def premium(self, ctx: Context):
        """Checkout Quotient Premium Plans."""
        await ctx.defer()
        guild = await Guild.get(pk=ctx.guild.id)
        premium_queue = await PremiumQueue.filter(guild_id=ctx.guild.id).prefetch_related("txn").order_by("created_at")

        t = TabularData()
        t.set_columns(["Tier", "Is Active "])

        for tier in GuildTier:
            t.add_row([tier.name.upper(), "✅" if guild.tier == tier else "❌"])

        embed = discord.Embed(color=self.bot.color)
        embed.description = f"Current Tier: ```\n{t.render()}\n```"

        if guild.is_premium:
            embed.add_field(
                name="Expires At",
                value=discord.utils.format_dt(guild.upgraded_until, "f"),
                inline=False,
            )

            embed.add_field(
                name="Upgraded By",
                value=f"**`{await self.bot.get_or_fetch_member(ctx.guild, guild.upgraded_by)}`**",
                inline=False,
            )

        upcoming_plans_text = ""
        for idx, pq in enumerate(premium_queue, start=1):
            txn = pq.txn
            upcoming_plans_text += f"`{idx}.`**{txn.tier.name}** - {naturaldelta(txn.premium_duration)}\n"

        if not premium_queue:
            upcoming_plans_text = "`Purchase Premium to add to queue.`"
        embed.add_field(name="Upcoming Premium", value=upcoming_plans_text, inline=False)
        embed.set_footer(text="Next upcoming plan auto applies after current plan ends.")

        v = discord.ui.View(timeout=None)
        v.add_item(UpgradeButton(label=("Purchase Tier")))
        v.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                url=self.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )

        await ctx.send(embed=embed, view=v)

    @commands.Cog.listener()
    async def on_premium_purchase(self, record: PremiumTxn):
        """
        Some 'not so important' tasks to be done after a successful premium purchase.
        This event is fired only in the Main bot.
        """

        member = self.bot.support_server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config("PREMIUM_ROLE_ID")), reason="They purchased premium.")


async def setup(bot: Quotient):
    await bot.add_cog(Premium(bot))
