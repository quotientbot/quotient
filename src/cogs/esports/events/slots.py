from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import discord

from core import Cog
from models import Scrim, ScrimsSlotManager, Timer


class SlotManagerEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_scrim_match_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if not scrim:
            return

        if not scrim.match_time == timer.expires:
            return

        record = await ScrimsSlotManager.get_or_none(guild_id=scrim.guild_id, scrim_ids__contains=scrim.id)
        if record:
            await record.refresh_public_message()

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        record = await ScrimsSlotManager.get_or_none(main_channel_id=channel.id)
        if not record:
            return
        await record.full_delete()

    @Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if not payload.guild_id:
            return

        record = await ScrimsSlotManager.get_or_none(message_id=payload.message_id)
        if not record:
            return

        await record.full_delete()
