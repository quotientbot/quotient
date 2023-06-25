from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import config
from constants import IST
from models import AutoPurge, EasyTag, Guild, Scrim, SSVerify, TagCheck, Tourney, BlockList


class CacheManager:
    def __init__(self, bot):
        if TYPE_CHECKING:
            from .Bot import Quotient

        self.bot: Quotient = bot

        self.guild_data = {}
        self.eztagchannels = set()
        self.tagcheck = set()
        self.scrim_channels = set()
        self.tourney_channels = set()
        self.autopurge_channels = set()
        self.media_partner_channels = set()
        self.ssverify_channels = set()

        self.blocked_ids = set()

    async def fill_temp_cache(self):
        async for record in Guild.all():
            self.guild_data[record.guild_id] = {
                "prefix": record.prefix,
                "color": record.embed_color or config.COLOR,
                "footer": record.embed_footer or config.FOOTER,
            }

        async for record in EasyTag.all():
            self.eztagchannels.add(record.channel_id)

        async for record in TagCheck.all():
            self.tagcheck.add(record.channel_id)

        async for record in Scrim.filter(opened_at__lte=datetime.now(tz=IST)).all():
            self.scrim_channels.add(record.registration_channel_id)

        async for record in Tourney.filter(started_at__not_isnull=True):
            self.tourney_channels.add(record.registration_channel_id)

        async for record in AutoPurge.all():
            self.autopurge_channels.add(record.channel_id)

        async for record in Tourney.all():
            async for partner in record.media_partners.all():
                self.media_partner_channels.add(partner.channel_id)

        async for record in SSVerify.all():
            self.ssverify_channels.add(record.channel_id)

        async for record in BlockList.all():
            self.blocked_ids.add(record.block_id)

    def guild_color(self, guild_id: int):
        return self.guild_data.get(guild_id, {}).get("color", config.COLOR)

    def guild_footer(self, guild_id: int):
        return self.guild_data.get(guild_id, {}).get("footer", config.FOOTER)

    async def update_guild_cache(self, guild_id: int, *, set_default=False) -> None:
        if set_default:
            await Guild.get(pk=guild_id).update(
                prefix=config.PREFIX, embed_color=config.COLOR, embed_footer=config.FOOTER
            )

        _g = await Guild.get(pk=guild_id)
        self.guild_data[guild_id] = {
            "prefix": _g.prefix,
            "color": _g.embed_color or config.COLOR,
            "footer": _g.embed_footer or config.FOOTER,
        }

    # @staticmethod
    # @cached(ttl=10, serializer=JsonSerializer())
    # async def match_bot_guild(guild_id: int, bot_id: int) -> bool:
    #     return await Guild.filter(pk=guild_id, bot_id=bot_id).exists()
