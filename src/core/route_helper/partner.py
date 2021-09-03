from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient


from models import Scrim, Partner
from constants import PartnerRequest


async def get_quo_partners(bot: Quotient, n: int = 0) -> dict:
    _list = []

    async for partner in Partner.filter(status=PartnerRequest.approved):
        guild = bot.get_guild(partner.guild_id)
        if not guild:
            continue

        _list.append(
            {
                "name": guild.name,
                "description": partner.description,
                "members": guild.member_count,
                "scrims": await Scrim.filter(guild_id=guild.id).count(),
                "icon": str(guild.icon.url) if guild.icon else None,
                "banner": str(guild.banner.url) if guild.banner else None,
                "invite": partner.invite,
            }
        )

    _list = sorted(_list, key=lambda x: x["scrims"], reverse=True)
    if n:

        _list = _list[:n]

    return {"ok": True, "result": _list}
