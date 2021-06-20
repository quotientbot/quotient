from core import Cog, Quotient, Context
from datetime import datetime, timedelta
import discord, asyncio, asyncpg
from discord.ext import commands
from models import Timer
from utils import IST, UserFriendlyTime, human_timedelta


class Reminders(Cog):
    """Reminders to do something."""

    def __init__(self, bot: Quotient):
        self.bot = bot
        self._have_data = asyncio.Event(loop=bot.loop)
        self._current_timer = None
        self._task = bot.loop.create_task(self.dispatch_timers())

    def cog_unload(self):
        self._task.cancel()

    async def get_active_timer(self, *, days=7):
        return await Timer.filter(expires__lte=datetime.now(tz=IST) + timedelta(days=days)).order_by("expires").first()

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

        if deleted == 0:  # Probably a task is already deleted or its expire time changed.
            return

        # dispatch the event
        event_name = f"{timer.event}_timer_complete"
        self.bot.dispatch(event_name, timer)

    async def dispatch_timers(self):
        try:
            while not self.bot.is_closed():
                timer = self._current_timer = await self.wait_for_active_timers(days=40)

                now = datetime.now(tz=IST)

                # print(now, timer.expires)

                if timer.expires >= now:
                    to_sleep = (timer.expires - now).total_seconds()
                    # print(to_sleep)
                    await asyncio.sleep(to_sleep)

                await self.call_timer(timer)

        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def short_timer_optimisation(self, seconds, timer):
        await asyncio.sleep(seconds)
        event_name = f"{timer.event}_timer_complete"
        self.bot.dispatch(event_name, timer)

    async def create_timer(self, *args, **kwargs):
        when, event, *args = args

        try:
            now = kwargs.pop("created")
        except KeyError:
            now = datetime.now(tz=IST)

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

    # @commands.group(aliases=("timer", "remind"), invoke_Without_command=True)
    # async def reminder(self, ctx: Context, *, when: UserFriendlyTime(commands.clean_content, default="\u2026")):
    #     """Reminds you of something after a certain amount of time.

    #     The input can be any direct date (e.g. YYYY-MM-DD) or a human
    #     readable offset. Examples:

    #     - "next thursday at 3pm do something funny"
    #     - "do the dishes tomorrow"
    #     - "in 3 days do the thing"
    #     - "2d unmute someone"

    #     Times are in IST.
    #     """
    #     expire = IST.localize(when.dt) + timedelta(hours=5, minutes=30)

    #     timer = await self.create_timer(
    #         expire,
    #         "reminder",
    #         ctx.author.id,
    #         ctx.channel.id,
    #         when.arg,
    #         message_id=ctx.message.id,
    #     )

    #     delta = human_timedelta(expire, source=timer.created)
    #     await ctx.send(f"Alright {ctx.author.mention}, in {delta}: {when.arg}")

    # @Cog.listener()
    # async def on_reminder_timer_complete(self, timer: Timer):
    #     author_id, channel_id, message = timer.args

    #     try:
    #         channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
    #     except discord.HTTPException:
    #         return

    #     guild_id = channel.guild.id if isinstance(channel, discord.TextChannel) else "@me"
    #     message_id = timer.kwargs.get("message_id")
    #     msg = f"<@{author_id}>, {human_timedelta(timer.created)}: {message}"

    #     if message_id:
    #         msg = f"{msg}\n\n<https://discord.com/channels/{guild_id}/{channel.id}/{message_id}>"

    #     try:
    #         await channel.send(msg)
    #     except discord.HTTPException:
    #         return


def setup(bot):
    bot.add_cog(Reminders(bot))
