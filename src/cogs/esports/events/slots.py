from __future__ import annotations
import typing

from core.decorators import right_bot_check

if typing.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Cog
from models import Scrim, Timer, SlotManager, SlotLocks

from datetime import datetime, timedelta
from constants import IST
from ..helpers import update_main_message, delete_slotmanager, send_sm_logs, SlotLogType


class SlotManagerEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    @right_bot_check()
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
        await self.bot.reminders.create_timer(new_time, "scrim_lock", scrim_id=scrim.id)

        await SlotLocks.filter(pk=scrim.id).update(locked=True, lock_at=new_time)
        await update_main_message(guild.id, self.bot)

        await send_sm_logs(
            sm,
            SlotLogType.private,
            f"SlotManager for Scrim {scrim.id} ({scrim.registration_channel.mention}) has been locked.\n\n"
            "The slots of this scrim can neither be claimed nor cancelled now.\n",
        )

    @Cog.listener()
    @right_bot_check()
    async def on_guild_channel_delete(self, channel):
        if not isinstance(channel, discord.TextChannel):
            return

        record = await SlotManager.get_or_none(main_channel_id=channel.id)
        if not record:
            return

        await delete_slotmanager(record, self.bot)

    @Cog.listener()
    @right_bot_check()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if not payload.guild_id:
            return

        record = await SlotManager.get_or_none(message_id=payload.message_id)
        if not record:
            return

        await delete_slotmanager(record, self.bot)
