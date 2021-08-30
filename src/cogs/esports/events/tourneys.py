from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog
from models import Tourney, TMSlot
from discord.ext import tasks

from ..helpers import (
    add_role_and_reaction,
    tourney_end_process,
    before_registrations,
    cannot_take_registration,
    check_tourney_requirements,
)
from unicodedata import normalize
from constants import EsportsLog

import discord
import asyncio
import utils

TourneyQueueMessage = typing.NamedTuple("TourneyQueueMessage", [("tourney", Tourney), ("message", discord.Message)])


class TourneyEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.tourney_queue = asyncio.Queue()
        self.tourney_registration_worker.start()

    def cog_unload(self):
        self.tourney_registration_worker.stop()

    @tasks.loop(seconds=2, reconnect=True)
    async def tourney_registration_worker(self):
        while not self.tourney_queue.empty():
            queue_message: TourneyQueueMessage = await self.tourney_queue.get()
            tourney, message = queue_message.tourney, queue_message.message

            ctx = await self.bot.get_context(message)

            teamname = utils.find_team(message)

            tourney = await Tourney.get_or_none(pk=tourney.id)  # Refetch Tourney to check get its updated instance

            if not tourney or tourney.closed:  # Tourney is deleted or not opened.
                continue

            assigned_slots = await tourney.assigned_slots.order_by("-id").first()

            numb = 0 if assigned_slots is None else assigned_slots.num
            slot = await TMSlot.create(
                leader_id=ctx.author.id,
                team_name=teamname,
                num=numb + 1,
                members=[m.id for m in message.mentions],
                jump_url=message.jump_url,
            )

            await tourney.assigned_slots.add(slot)

            self.bot.loop.create_task(add_role_and_reaction(ctx, tourney.role))

            self.bot.dispatch(
                "tourney_log",
                EsportsLog.success,
                tourney,
                message=ctx.message,
                assigned_slot=slot,
                num=numb + 1,
            )

            if tourney.total_slots == numb + 1:
                await tourney_end_process(ctx, tourney)

    @Cog.listener("on_message")
    async def on_tourney_registration(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        if channel_id not in self.bot.tourney_channels:
            return

        tourney = await Tourney.get_or_none(registration_channel_id=channel_id)

        if tourney is None:
            return self.bot.tourney_channels.discard(channel_id)

        if tourney.started_at is None:
            return

        modrole = tourney.modrole

        if modrole is not None and modrole in message.author.roles:
            return

        if not before_registrations(message, tourney.role):
            return await cannot_take_registration(message, tourney)

        message.content = normalize("NFKC", message.content.lower())

        if not await check_tourney_requirements(self.bot, message, tourney):
            return

        if not self.tourney_registration_worker.next_iteration or self.tourney_registration_worker.failed():
            # if for any fking reason its stopped , we want it to start again
            self.tourney_registration_worker.start()

        self.tourney_queue.put_nowait(TourneyQueueMessage(tourney, message))
