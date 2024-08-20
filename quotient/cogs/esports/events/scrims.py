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
    ensure_self_scrims_permissions,
    find_team_name,
    get_today_day,
)
from tortoise.query_utils import Prefetch

from quotient.models import (
    Scrim,
    ScrimAssignedSlot,
    ScrimReservedSlot,
    ScrimsBanLog,
    ScrimsBannedUser,
    ScrimsSlotManager,
    Timer,
)


class ScrimsEvents(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.scrim_registration_lock = asyncio.Lock()
        self.scrim_autoclean_lock = asyncio.Lock()

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

        if not scrim.reg_started_at:
            return

        if Scrim.is_ignorable(msg.author):
            return

        if not await ensure_self_scrims_permissions(scrim):
            return self.bot.cache.scrim_channel_ids.discard(channel_id)

        msg.content = normalize("NFKC", msg.content.lower().strip())

        if not await ensure_scrims_requirements_in_msg(scrim, msg):
            return

        async with self.scrim_registration_lock:
            team_name = find_team_name(msg.content)
            if not team_name:
                team_name = f"{msg.author}'s Team"

            scrim = await Scrim.get_or_none(pk=scrim.pk)
            if scrim is None or not scrim.reg_started_at:
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

            self.bot.loop.create_task(scrim.add_tick(msg))

            if len(scrim.available_slots) == 1:
                try:
                    await scrim.close_registration()
                except Exception as e:
                    await scrim.send_log(
                        f"Error closing registration of {scrim.id}: {e}",
                        title="Scrim Registration Close Error",
                        color=discord.Color.red(),
                        ping_scrims_mod=True,
                        add_contact_btn=True,
                    )

                else:
                    await scrim.send_log(
                        f"{scrim}, registration has been closed.",
                        title="Scrim Registration Closed",
                        color=discord.Color.green(),
                        add_contact_btn=False,
                    )

    @commands.Cog.listener()
    async def on_scrim_reg_start_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id).prefetch_related(
            Prefetch("reserved_slots", queryset=ScrimReservedSlot.all().order_by("num"))
        )
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

        if scrim.reg_started_at and scrim.reg_started_at.strftime("%d-%b-%Y %I:%M %p") == self.bot.current_time.strftime(
            "%d-%b-%Y %I:%M %p"
        ):
            return

        guild = scrim.guild

        if not guild:
            return

        if not await ensure_self_scrims_permissions(scrim):
            return

        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())

        try:
            await scrim.start_registration()
        except Exception as e:
            self.bot.logger.error(f"Error starting registration of {scrim.id}: {e}")

    @commands.Cog.listener()
    async def on_scrim_reg_end_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if not scrim:
            return

        scrim.reg_auto_end_time += timedelta(hours=24)
        await scrim.save(update_fields=["reg_auto_end_time"])

        await self.bot.reminders.create_timer(scrim.reg_auto_end_time, "scrim_reg_end", scrim_id=scrim.id)

        if scrim.reg_ended_at:  # already ended
            return

        try:
            await scrim.close_registration()
        except Exception as e:
            await scrim.send_log(
                f"Error auto closing registration of {scrim.id}: {e}",
                title="Scrim Auto End Error",
                color=discord.Color.red(),
                ping_scrims_mod=True,
            )

        else:
            await scrim.send_log(
                f"{scrim}, registration has been automatically closed.",
                title="Scrim Registration Closed",
                color=discord.Color.green(),
                add_contact_btn=False,
            )

    @commands.Cog.listener()
    async def on_scrim_channel_autoclean_timer_complete(self, timer: Timer):
        """
        Autocleans scrims registration msges at the set time.
        """
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id)
        if not scrim:  # deleted probably
            return

        if timer.expires != scrim.autoclean_channel_time:
            return

        next_autoclean_time = scrim.autoclean_channel_time + timedelta(hours=24)

        scrim.autoclean_channel_time = next_autoclean_time
        await scrim.save(update_fields=["autoclean_channel_time"])
        await self.bot.reminders.create_timer(scrim.autoclean_channel_time, "autoclean_scrims_channel", scrim_id=scrim.id)

        if not scrim.scrim_status:  # Scrim is disabled
            return

        if scrim.reg_ended_at and scrim.reg_ended_at < self.bot.current_time - timedelta(hours=48):
            return

        guild = scrim.guild
        if not guild:
            return

        if not guild.chunked:
            self.bot.loop.create_task(guild.chunk())

        registration_channel = scrim.registration_channel
        if not registration_channel:
            return

        if not registration_channel.permissions_for(guild.me).manage_messages:
            return await scrim.send_log(
                f"I couldn't autoclean {scrim}, because I don't have `Manage Messages` permission in that channel.",
                title="Autoclean Failed",
                color=discord.Color.red(),
                ping_scrims_mod=True,
            )

        async with self.scrim_autoclean_lock:
            try:
                await registration_channel.purge(limit=70, check=lambda msg: not msg.pinned, reason="Scrims Autoclean")
            except discord.HTTPException:
                pass
            else:
                await scrim.send_log(
                    f"{scrim}, registration messages have been autocleaned.",
                    title="Scrim Autoclean",
                    color=discord.Color.green(),
                )
                await asyncio.sleep(7)

    @commands.Cog.listener()
    async def on_scrim_ban_timer_complete(self, timer: Timer):
        ban_id = timer.kwargs["ban_id"]

        record = await ScrimsBannedUser.get_or_none(pk=ban_id)
        if not record:
            return

        await record.delete()

        banlog = await ScrimsBanLog.get_or_none(guild_id=record.guild_id)
        if not banlog:
            return

        await banlog.log_unban(record, self.bot.user)

    @commands.Cog.listener()
    async def on_scrim_slot_reserve_timer_complete(self, timer: Timer):
        reserve_id = timer.kwargs["reserve_id"]

        record = await ScrimReservedSlot.get_or_none(pk=reserve_id).prefetch_related("scrim")
        if not record:
            return

        if record.scrim is None:
            return

        guild = record.scrim.guild
        if not guild:
            return

        await record.delete()
        await record.scrim.send_log(
            f"**Slot {record.num} ({record.team_name} - {record.leader})** will no longer be reserved, because the time limit has expired.",
            title="Slot Unreserved",
            color=discord.Color.red(),
        )

    @commands.Cog.listener()
    async def on_scrims_match_start_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id).prefetch_related("slotm")
        if not scrim:
            return

        if not scrim.match_start_time == timer.expires:
            return

        if scrim.slotm:
            await scrim.slotm.refresh_public_message()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        slotm = await ScrimsSlotManager.get_or_none(channel_id=channel.id)
        if slotm:
            await slotm.full_delete()

        scrim = await Scrim.get_or_none(registration_channel_id=channel.id)
        if scrim:
            await scrim.full_delete()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if not payload.guild_id:
            return

        record = await ScrimsSlotManager.get_or_none(message_id=payload.message_id)
        if not record:
            return

        await record.full_delete()
