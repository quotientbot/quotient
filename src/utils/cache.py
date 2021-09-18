from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from datetime import datetime
from constants import IST
import models
import config


async def cache(bot: Quotient):
    # until we implement redis

    records = await models.Guild.all()
    for record in records:
        bot.guild_data[record.guild_id] = {
            "prefix": record.prefix,
            "color": record.embed_color or config.COLOR,
            "footer": record.embed_footer or config.FOOTER,
        }

    records = models.EasyTag.all()
    async for record in records:
        bot.eztagchannels.add(record.channel_id)

    records = models.TagCheck.all()
    async for record in records:
        bot.tagcheck.add(record.channel_id)

    records = models.Scrim.filter(opened_at__lte=datetime.now(tz=IST)).all()
    async for record in records:
        bot.scrim_channels.add(record.registration_channel_id)

    records = models.Tourney.filter(started_at__not_isnull=True)
    async for record in records:
        bot.tourney_channels.add(record.registration_channel_id)

    async for record in models.AutoPurge.all():
        bot.autopurge_channels.add(record.channel_id)

    async for record in models.Tourney.all():
        async for partner in record.media_partners.all():
            bot.media_partner_channels.all(partner.channel_id)
