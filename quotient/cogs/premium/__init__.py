from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord.ext import commands

from quotient.lib import TabularData, random_greeting_msg, random_thanks_image
from quotient.models import Guild, PremiumTxn
from quotient.models.others.premium import GuildTier

from .checks import *
from .views import *


class Premium(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    async def pstatus(self, ctx: Context):
        """Get current server's premium status."""
        guild = await Guild.get(pk=ctx.guild.id)

        t = TabularData()
        t.set_columns(["Tier", "Is Active "])

        for tier in GuildTier:
            t.add_row([tier.name.upper(), "✅" if guild.tier == tier else "❌"])

        embed = discord.Embed(color=self.bot.color)
        embed.add_field(
            name="Server Tier",
            value=f"```\n{t.render()}\n```",
            inline=False,
        )

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

        v = discord.ui.View(timeout=None)
        v.add_item(UpgradeButton(label=("Upgrade Server" if not guild.is_premium else "Extend / Renew Quotient Pro")))

        return await ctx.reply(embed=embed, view=v)

    @commands.hybrid_command(aliases=("perks", "pro"))
    async def premium(self, ctx: Context):
        """Checkout Quotient Premium Plans."""

        g = await Guild.get(pk=ctx.guild.id)

        await prompt_premium_plan(ctx, f"Current Tier: **{g.tier.name}**")

    @commands.Cog.listener()
    async def on_premium_purchase(self, txnId: str):
        record = await PremiumTxn.get(txnid=txnId)

        upgraded_guild_asyncpg = await self.bot.my_pool.fetchrow("SELECT * FROM guilds WHERE guild_id = $1", record.guild_id)
        await self.bot.pro_pool.execute(
            """
            INSERT INTO guilds (guild_id, prefix, tier, upgraded_by, upgraded_until)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (guild_id)
            DO UPDATE SET tier = $3, upgraded_by = $4, upgraded_until = $5""",
            record.guild_id,
            self.bot.default_prefix,
            True,
            upgraded_guild_asyncpg["premium_end_time"],
            record.user_id,
        )

        member = self.bot.support_server.get_member(record.user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config("PREMIUM_ROLE_ID")), reason="They purchased premium.")

        else:
            member = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, record.user_id)

        _e = discord.Embed(color=discord.Color.gold(), description=f"Thanks **{member}** for purchasing Quotient Premium.")
        _e.set_image(url=random_thanks_image())
        await self.hook.send(embed=_e, username="premium-logs", avatar_url=self.bot.config("PRO_BOT_AVATAR_URL"))

        upgraded_guild = self.bot.get_guild(record.guild_id)
        _guild = await Guild.get_or_none(pk=record.guild_id)

        _e = discord.Embed(
            color=self.bot.color,
            title="Quotient Pro Purchase Successful!",
            url=self.bot.config("SUPPORT_SERVER_LINK"),
            description=(
                f"{random_greeting_msg()} {member.mention},\n"
                f"Thanks for purchasing Quotient Premium. Your server **__{upgraded_guild}__** "
                f"has access to Quotient Pro features until `{_guild.premium_end_time.strftime('%d-%b-%Y %I:%M %p')} IST`.\n\n"
            ),
        )

        v = discord.ui.View(timeout=None)
        v.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Join Support Server", url=self.bot.config("SUPPORT_SERVER_LINK"))
        )
        v.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Invite Quotient Pro", url=self.bot.config("PRO_INVITE_LINK"))
        )

        try:
            await member.send(embed=_e, view=v)
        except discord.HTTPException:
            pass


async def setup(bot: Quotient):
    await bot.add_cog(Premium(bot))
