from datetime import datetime, timedelta
from core import Quotient, Cog, Context
from models import Snipes
from utils import IST


__all__ = ("LoggingEvents",)


class LoggingEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.loop.create_task(self.delete_older_snipes())

    async def delete_older_snipes(self):  # we delete snipes that are older than 15 days
        await Snipes.filter(delete_time__lte=(datetime.now(tz=IST) - timedelta(days=15))).all().delete()

    @Cog.listener()
    async def on_snipe_deleted(self, message):
        if not message.guild:
            return
        channel = message.channel
        content = message.content if message.content else "*[Content Unavailable]*"

        await Snipes.create(channel_id=channel.id, content=content, nsfw=channel.is_nsfw())
