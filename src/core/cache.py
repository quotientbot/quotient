from __future__ import annotations

from aiocache import cached
from aiocache.serializers import PickleSerializer

from typing import Union, TYPE_CHECKING


from models import Guild, EasyTag, TagCheck, Scrim, Tourney, AutoPurge
import config
from constants import IST
from datetime import datetime
import discord


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

    @cached(ttl=60, serializer=PickleSerializer())
    async def match_bot_guild(self, guild: Union[discord.Guild, int], bot_id: int) -> bool:
        if isinstance(guild, int):
            guild = self.bot.get_guild(guild)

        if not guild:
            return False

        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())

        _g = await Guild.get(pk=guild.id)

        _m_quo = 746348747918934096
        _p_quo = 846339012607082506

        if _g.is_premium:
            if _p_quo in (m.id for m in guild.members):
                return bot_id == _p_quo
            else:
                return _m_quo == bot_id

        else:
            return _m_quo == bot_id
