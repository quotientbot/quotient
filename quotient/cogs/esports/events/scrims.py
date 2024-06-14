from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import asyncio
from datetime import timedelta
from unicodedata import normalize

import discord
from discord.ext import commands
from lib import (
    ensure_scrims_requirements_in_msg,
    ensure_self_permissions,
    find_team_name,
    get_today_day,
)
from models import Scrim, ScrimAssignedSlot, ScrimReservedSlot, Timer
from tortoise.query_utils import Prefetch


class ScrimsEvents(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.scrim_registration_lock = asyncio.Lock()

    @commands.Cog.listener(name="on_message")
    async def on_scrims_registration_msg(self, msg: discord.Message):
        if not msg.guild or msg.author.bot:
            return

        channel_id = msg.channel.id
        if channel_id not in self.bot.cache.scrim_channel_ids:
            return

        scrim = await Scrim.get_or_none(registration_channel_id=channel_id)

        if scrim is None:
            return self.bot.cache.scrim_channel_ids.discard(channel_id)

        if not scrim.started_at:
            return

        if Scrim.is_ignorable(msg.author):
            return

        if not await ensure_self_permissions(scrim):
            return self.bot.cache.scrim_channel_ids.discard(channel_id)

        msg.content = normalize("NFKC", msg.content.lower().strip())

        if not await ensure_scrims_requirements_in_msg(scrim, msg):
            return

        async with self.scrim_registration_lock:
            team_name = find_team_name(msg.content)
            if not team_name:
                team_name = f"{msg.author}'s Team"

            scrim = await Scrim.get_or_none(pk=scrim.pk)
            if scrim is None or not scrim.started_at:
                return

            try:
                slot_num = scrim.available_slots[0]
            except IndexError:
                return

            team_members = {msg.author.id}
            for m in msg.mentions:
                if not m.bot:
                    team_members.add(m.id)

            team_members = list(team_members)

            await ScrimAssignedSlot.create(
                num=slot_num,
                leader_id=team_members[0],
                team_name=team_name,
                members=team_members,
                jump_url=msg.jump_url,
                scrim=scrim,
            )

            await Scrim.get(pk=scrim.pk).update(available_slots=scrim.available_slots[1:])

            self.bot.loop.create_task(scrim.add_tick_and_role(msg))

            if len(scrim.available_slots) == 1:
                try:
                    await scrim.close_registration()
                except Exception as e:
                    self.bot.logger.error(f"Error closing registration of {scrim.id}: {e}")

    @commands.Cog.listener()
    async def on_scrim_open_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id).prefetch_related(
            Prefetch("reserved_slots", queryset=ScrimReservedSlot.all().order_by("num"))
        )  # type: Scrim
        if not scrim:
            return

        if scrim.reg_start_time != timer.expires:
            return

        scrim.reg_start_time += timedelta(hours=24)
        await scrim.save(update_fields=["reg_start_time"])

        await self.bot.reminders.create_timer(
            scrim.reg_start_time,
            "scrim_open",
            scrim_id=scrim.id,
        )

        if not scrim.scrim_status or not get_today_day() in scrim.registration_open_days:
            return

        if scrim.started_at and scrim.started_at.strftime("%d-%b-%Y %I:%M %p") == self.bot.current_time.strftime(
            "%d-%b-%Y %I:%M %p"
        ):
            return

        guild = scrim.guild

        if not guild:
            return

        if not await ensure_self_permissions(scrim):
            return

        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())

        try:
            await scrim.start_registration()
        except Exception as e:
            self.bot.logger.error(f"Error starting registration of {scrim.id}: {e}")
