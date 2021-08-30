from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import discord
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

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not isinstance(channel, discord.TextChannel):
            return

        record = await SlotManager.get_or_none(main_channel_id=channel.id)
        if not record:
            return

        scrims = await Scrim.filter(guild_id=record.guild_id)
        await SlotManager.filter(pk=record.id).delete()
        await SlotLocks.filter(pk__in=(scrim.id for scrim in scrims)).delete()

    @Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if not payload.guild_id:
            return

        record = await SlotManager.get_or_none(message_id=payload.message_id)
        if not record:
            return

        scrims = await Scrim.filter(guild_id=record.guild_id)
        await SlotManager.filter(pk=record.id).delete()
        await SlotLocks.filter(pk__in=(scrim.id for scrim in scrims)).delete()
