from utils import EventType, IST
from core import Cog, Quotient
from models import Autoevent
from discord.ext import tasks
import itertools

from datetime import datetime, timedelta


__all__ = ("Funevents",)


class Funevents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.autoevent_dispatcher.start()

    def cog_unload(self):
        self.autoevent_dispatcher.cancel()

    async def handle_event(self, _type, records):
        if _type == EventType.meme:
            print("automeme bruh")

    @tasks.loop(seconds=60)
    async def autoevent_dispatcher(self):
        current_time = datetime.now(tz=IST)
        records = await Autoevent.all().filter(webhook__isnull=False, send_time__lte=current_time, toggle=True)
        if not len(records):
            return

        for key, group in itertools.groupby(records, key=lambda rec: rec.type):
            self.bot.loop.create_task(self.handle_event(key, list(group)))

        to_update = [record.id for record in records]
        # now , can tortoise-orm do this?
        await self.bot.db.execute(
            "UPDATE autoevents set send_time = autoevents.send_time + autoevents.interval * interval '1 minute' where autoevents.id = any($1::bigint[])",
            to_update,
        )

    @autoevent_dispatcher.before_loop
    async def before_autoevent_dispatcher(self):
        await self.bot.wait_until_ready()
