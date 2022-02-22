from __future__ import annotations

from discord.ext import commands
import discord

import typing as T

__all__ = ("QuotientRatelimiter",)


class CooldownByMember(commands.CooldownMapping):
    def _bucket_key(self, member: discord.Member):
        return member.id


class CooldownByGuild(commands.CooldownMapping):
    def _bucket_key(self, member: discord.Guild):
        return member.id


class QuotientRatelimiter:
    def __init__(self, rate: float, per: float):
        self.by_member = CooldownByMember.from_cooldown(rate, per, commands.BucketType.member)
        self.by_guild = CooldownByGuild.from_cooldown(rate, per, commands.BucketType.guild)

    def is_ratelimited(self, obj: T.Union[discord.Guild, discord.Member]) -> bool:
        if isinstance(obj, discord.Guild):
            return self.by_guild.get_bucket(obj).update_rate_limit()

        return self.by_member.get_bucket(obj).update_rate_limit()
