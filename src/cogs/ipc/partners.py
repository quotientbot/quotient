from __future__ import annotations

import typing
import discord

if typing.TYPE_CHECKING:
    from core import Quotient


from constants import PartnerRequest
from .base import IpcCog
from discord.ext import ipc

from models import Scrim, Partner


class QuoPartners(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @ipc.server.route()
    async def get_quo_partners(self, payload):
        _list = []

        async for partner in Partner.filter(status=PartnerRequest.approved):
            guild: discord.Guild = self.bot.get_guild(partner.guild_id)
            if not guild:
                continue

            _list.append(
                {
                    "name": guild.name,
                    "description": partner.description,
                    "members": guild.member_count,
                    "scrims": await Scrim.filter(pk=guild.id).count(),
                    "icon": str(guild.icon_url),
                    "banner": str(guild.banner_url),
                    "invite": partner.invite,
                }
            )

        if payload.n:
            _list = _list[: payload.n]

        return {"ok": True, "result": sorted(_list, key=lambda x: x["scrims"], reverse=True)}
