from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt

from quotient.cogs.dev.consts import PRIVATE_GUILD_IDS
from quotient.cogs.dev.stats import DevStats


class DevCommands(commands.Cog, name="Developer"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    bl_group = app_commands.Group(
        name="blacklist",
        description="Manage blacklist",
        guild_only=True,
        guild_ids=PRIVATE_GUILD_IDS,
    )

    @bl_group.command(name="add")
    async def bl_add(
        self,
        inter: discord.Interaction,
        target_type: T.Literal["user", "guild"],
        target: str,
        reason: str,
    ):
        """
        Add a user or guild to the blacklist.
        """
        if target in self.bot.blacklist.all_blacklisted():
            return await inter.response.send_message(
                embed=self.bot.error_embed(f"{target} [{target_type}] is already blacklisted."), ephemeral=True
            )

        await self.bot.blacklist.put(target, reason, target_type, self.bot.current_time.isoformat(), str(inter.user.id))
        await inter.response.send_message(
            embed=self.bot.success_embed(f"{target} [{target_type}] has been blacklisted."), ephemeral=True
        )

    @bl_group.command(name="remove")
    async def bl_remove(
        self,
        inter: discord.Interaction,
        target: str,
    ):
        """
        Remove a user or guild from the blacklist.
        """
        if target not in self.bot.blacklist.all_blacklisted():
            return await inter.response.send_message(embed=self.bot.error_embed(f"{target} is not blacklisted."), ephemeral=True)

        await self.bot.blacklist.remove(target)
        await inter.response.send_message(
            embed=self.bot.success_embed(description=f"{target} has been unblacklisted."), ephemeral=True
        )

    @bl_group.command(name="list")
    async def bl_list(self, inter: discord.Interaction):
        """
        List all blacklisted users and guilds.
        """
        bl = self.bot.blacklist.all_blacklisted()
        if not bl:
            return await inter.response.send_message(embed=self.bot.error_embed("No one is blacklisted."), ephemeral=True)

        e = discord.Embed(color=self.bot.color, title="Blacklist", description="")
        for idx, (k, v) in enumerate(bl.items(), start=1):
            obj = self.bot.get_user(int(k)) if v["type"] == "user" else self.bot.get_guild(int(k))
            e.description += f"`{idx}.` `{obj or k}` [`{v['type']}`] - {v['reason']}\n"

        await inter.response.send_message(embed=e, ephemeral=True)

    @bl_group.command(name="info")
    async def bl_info(self, inter: discord.Interaction, target: str):
        """
        Get info about a blacklisted user or guild.
        """
        bl = self.bot.blacklist.all_blacklisted()
        if target not in bl:
            return await inter.response.send_message(embed=self.bot.error_embed(f"{target} is not blacklisted."), ephemeral=True)

        v = bl[target]
        obj = self.bot.get_user(str(target)) if v["type"] == "user" else self.bot.get_guild(str(target))

        e = discord.Embed(color=self.bot.color, title="Blacklist Info")
        e.description = (
            f"Obj: `{obj or target}` [`{v['type']}`]\n"
            f"Reason: {v['reason']}\n"
            f"Blacklisted At: {format_dt(datetime.fromisoformat(v['at']))}\n"
            f"Blacklisted By: {self.bot.get_user(int(v['by']))}"
        )

        await inter.response.send_message(embed=e, ephemeral=True)


async def setup(bot: Quotient):
    await bot.add_cog(DevCommands(bot))
    await bot.add_cog(DevStats(bot))
