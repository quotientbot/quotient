from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog
import discord


class LogEvents(Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot
        self.guild_log = discord.Webhook.from_url(self.bot.config.GUILD_LOGS, session=self.bot.session)

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.guild_log.send(
            "```diff\n"
            f"+ [Joined] {guild.name} ({guild.id})\n"
            f"+ Owner: {guild.owner} ({guild.owner_id})\n"
            f"+ Members: {guild.member_count}\n"
            f"+ Created at: {guild.created_at.strftime('%d/%m/%Y, %H:%M')}\n"
            "```"
        )

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.guild_log.send(
            "```diff\n"
            f"- [Left] {guild.name} ({guild.id})\n"
            f"- Owner: {guild.owner} ({guild.owner_id})\n"
            f"- Members: {guild.member_count}\n"
            f"- Created at: {guild.created_at.strftime('%d/%m/%Y, %H:%M')}\n"
            f"- Joined at: {guild.me.joined_at.strftime('%d/%m/%Y, %H:%M')}\n"
            "```"
        )
