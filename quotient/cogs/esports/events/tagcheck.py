from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from discord.ext import commands
from lib import CROSS, TICK, find_team_name, plural
from models import TagCheck


class TagCheckEvents(commands.Cog):
    def __init__(self, bot: Quotient) -> None:
        self.bot = bot

    @commands.Cog.listener(name="on_message")
    async def on_tagcheck_msg(self, message: discord.Message):

        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        if not channel_id in self.bot.cache.tagcheck_channel_ids:
            return

        tc = await TagCheck.get_or_none(channel_id=channel_id, guild_id=message.guild.id)

        if not tc:
            return self.bot.cache.tagcheck_channel_ids.discard(channel_id)

        ignore_role = tc.ignorerole_role

        if ignore_role is not None and ignore_role in message.author.roles:
            return

        issues: list[str] = []
        team_name = find_team_name(message.content)

        if not team_name:
            issues.append("- Team Name not found in your registration format.")

        if tc.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
            issues.append("- You can't mention bots in your registration message.")

        if tc.required_mentions and not len(message.mentions) >= tc.required_mentions:
            issues.append(f"- You need to mention atleast `{plural(tc.required_mentions):teammate|teammates}`.")

        await message.add_reaction((CROSS, TICK)[not issues])
        if issues:
            return await message.reply(
                embed=discord.Embed(color=discord.Color.red(), description="\n".join(issues), title="Issues found!")
            )

        embed = discord.Embed(color=discord.Color.green())
        embed.description = f"Team Name: **{team_name}**\nPlayer(s): {(', '.join(m.mention for m in message.mentions)) if message.mentions else message.author.mention}"
        await message.reply(embed=embed)
