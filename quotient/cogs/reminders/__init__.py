from __future__ import annotations

import asyncio
import typing as T
from datetime import timedelta

import asyncpg
import discord

if T.TYPE_CHECKING:
    from core import Quotient

from discord.ext import commands
from models import Timer


class Reminders(commands.Cog):
    """Manages timers for various bot tasks."""

    def __init__(self, bot: Quotient):
        self.bot = bot
        self._have_data = asyncio.Event()
        self._current_timer = None
        self._task = bot.loop.create_task(self.dispatch_timers())

    def cog_unload(self):
        self._task.cancel()

    async def get_active_timer(self, *, days=7):
        return (
            await Timer.filter(
                expires__lte=self.bot.current_time + timedelta(days=days)
            )
            .order_by("expires")
            .first()
        )

    async def wait_for_active_timers(self, *, days=7):
        timer = await self.get_active_timer(days=days)
        if timer is not None:
            self._have_data.set()
            return timer

        self._have_data.clear()
        self._current_timer = None
        await self._have_data.wait()
        return await self.get_active_timer(days=days)

    async def call_timer(self, timer: Timer):
        # delete the timer
        deleted = await Timer.filter(pk=timer.id, expires=timer.expires).delete()

        if (
            deleted == 0
        ):  # Probably a task is already deleted or its expire time changed.
            return

        # dispatch the event
        event_name = f"{timer.event}_timer_complete"
        self.bot.dispatch(event_name, timer)

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                timer = self._current_timer = await self.wait_for_active_timers(days=40)

                now = self.bot.current_time

                # print(now, timer.expires)

                if timer.expires >= now:
                    to_sleep = (timer.expires - now).total_seconds()
                    # print(to_sleep)
                    await asyncio.sleep(to_sleep)

                await self.call_timer(timer)
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def short_timer_optimisation(self, seconds, timer: Timer):
        await asyncio.sleep(seconds)
        event_name = f"{timer.event}_timer_complete"
        self.bot.dispatch(event_name, timer)

    async def create_timer(self, *args, **kwargs):
        when, event, *args = args

        try:
            now = kwargs.pop("created")
        except KeyError:
            now = self.bot.current_time

        delta = (when - now).total_seconds()

        timer = await Timer.create(
            expires=when,
            created=now,
            event=event,
            extra={"kwargs": kwargs, "args": args},
        )

        # only set the data check if it can be waited on
        if delta <= (86400 * 40):  # 40 days
            self._have_data.set()

        # check if this timer is earlier than our currently run timer
        if self._current_timer and when < self._current_timer.expires:
            # cancel the task and re-run it
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

        return timer

    @commands.Cog.listener()
    async def on_test_timer_complete(self, timer: Timer):
        self.bot.logger.info(f"Test timer complete: {timer}")


async def setup(bot: Quotient):
    await bot.add_cog(Reminders(bot))
