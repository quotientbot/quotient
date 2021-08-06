from datetime import datetime
from constants import IST
import models
import config


async def cache(bot):
    # until we implement redis

    records = await models.Guild.all()
    bot.guild_data = {}

    for record in records:
        bot.guild_data[record.guild_id] = {
            "prefix": record.prefix,
            "color": record.embed_color or config.COLOR,
            "footer": record.embed_footer or config.FOOTER,
        }

    records = models.EasyTag.all()
    bot.eztagchannels = set()
    async for record in records:
        bot.eztagchannels.add(record.channel_id)

    records = models.TagCheck.all()
    bot.tagcheck = set()
    async for record in records:
        bot.tagcheck.add(record.channel_id)

    records = models.Scrim.filter(opened_at__lte=datetime.now(tz=IST)).all()
    bot.scrim_channels = set()
    async for record in records:
        bot.scrim_channels.add(record.registration_channel_id)

    records = models.Tourney.filter(started_at__not_isnull=True)
    bot.tourney_channels = set()
    async for record in records:
        bot.tourney_channels.add(record.registration_channel_id)

    records = models.SSVerify.all()
    bot.ssverify_channels = set()
    async for record in records:
        bot.ssverify_channels.add(record.msg_channel_id)

    bot.autopurge_channels = set()
    async for record in models.AutoPurge.all():
        bot.autopurge_channels.add(record.channel_id)
