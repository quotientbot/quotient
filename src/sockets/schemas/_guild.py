import typing as T
import discord
from pydantic import BaseModel
from models import Guild

__all__ = ("QGuild",)


class QGuild(BaseModel):
    id: int
    channels: T.List[dict]
    roles: T.List[dict]
    boosted_by: T.List[dict]

    @staticmethod
    async def from_guild(guild: discord.Guild, perms: int):
        _d = {"id": guild.id, "dashboard_access": perms}
        _d["channels"] = [{"id": c.id, "name": c.name} for c in guild.text_channels]
        _d["roles"] = [{"id": r.id, "name": r.name} for r in guild.roles]
        _d["boosted_by"] = {}

        record = await Guild.get(pk=guild.id)
        if record.is_premium:
            booster = await record.bot.get_or_fetch_member(guild, record.made_premium_by)
            _d["boosted_by"] = {
                "id": getattr(booster, "id", 12345),
                "username": getattr(booster, "name", "Unknown User"),
                "discriminator": getattr(booster, "discriminator", "#0000"),
                "avatar": booster.display_avatar.url,
            }

        return QGuild(**_d)
