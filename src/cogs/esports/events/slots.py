from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog
from models import Scrim, Timer, SlotManager, SlotLocks

from datetime import datetime, timedelta
from constants import IST
from ..helpers import update_main_message


class SlotManagerEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_scrim_lock_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]
        scrim = await Scrim.get_or_none(pk=scrim_id)
        if not scrim:
            return

        if (guild := scrim.guild) is None:
            return

        sm = await SlotManager.get_or_none(guild_id=guild.id)
        if not sm:
            return

        lock = await sm.locks.filter(pk=scrim.id).first()
        if lock.lock_at != timer.expires:
            return

        new_time = datetime.now(tz=IST) + timedelta(hours=24)
        await SlotLocks.filter(pk=scrim.id).update(locked=True, lock_at=new_time)
        await update_main_message(guild.id)

        await self.bot.reminders.create_timer(new_time, "scrim_lock", scrim_id=scrim.id)
