from __future__ import annotations

from discord.ext import commands
import discord

__all__ = ("MemberRatelimiter",)


class CooldownByMember(commands.CooldownMapping):
    def _bucket_key(self, member: discord.Member):
        return member.id


class MemberRatelimiter:
    def __init__(self, rate: float, per: float):
        self.by_member = CooldownByMember.from_cooldown(rate, per, commands.BucketType.member)

    def is_ratelimited(self, obj: discord.Member) -> bool:
        _bucket = self.by_member.get_bucket(obj)
        return _bucket.update_rate_limit()
