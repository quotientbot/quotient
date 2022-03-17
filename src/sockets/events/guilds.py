from __future__ import annotations

import typing as T

import discord

if T.TYPE_CHECKING:
    from core import Quotient

from models import Guild
from core import Cog
from ..schemas import QGuild

__all__ = ("SockGuild",)


class SockGuild(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_request__get_guilds(self, u, data: dict):
        guild_ids = data["guild_ids"]
        user_id = data["user_id"]

        results: T.List[QGuild] = []

        for _id in guild_ids:
            guild = self.bot.get_guild(int(_id))
            if not guild:
                continue

            member = await self.bot.get_or_fetch_member(guild, user_id)
            if not member:
                continue

            results.append(await QGuild.from_guild(guild, await self.__guild_permissions(guild, member)))

        await self.bot.sio.emit("get_guilds__{0}".format(u), [_.dict() for _ in results])

    async def __guild_permissions(self, guild: discord.Guild, user: discord.Member):
        perms = 1

        if user.guild_permissions.manage_guild:
            return 2

        g = await Guild.get(pk=guild.id)
        _roles = [str(_.id) for _ in user.roles]

        if any(i in g.dashboard_access["embed"] for i in _roles):
            perms *= 3

        if any(i in g.dashboard_access["scrims"] for i in _roles):
            perms *= 5

        if any(i in g.dashboard_access["tourney"] for i in _roles):
            perms *= 7

        if any(i in g.dashboard_access["slotm"] for i in _roles):
            perms *= 11

        return perms
