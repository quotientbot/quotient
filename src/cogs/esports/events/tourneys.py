from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog
from models import Tourney, TMSlot

from ..helpers import (
    add_role_and_reaction,
    tourney_end_process,
    before_registrations,
    cannot_take_registration,
    check_tourney_requirements,
    send_success_message,
)
from unicodedata import normalize
from constants import EsportsLog, RegDeny

import discord
import asyncio
import utils


class TourneyEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.__tourney_lock = asyncio.Lock()

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

        async with self.__tourney_lock:

            teamname = utils.find_team(message)

            tourney = await Tourney.get_or_none(pk=tourney.id)  # Refetch Tourney to check get its updated instance

            if not tourney or tourney.closed:  # Tourney is deleted or not opened.
                return

            if tourney.no_duplicate_name:
                async for slot in tourney.assigned_slots.all():
                    if slot.team_name == teamname:
                        return self.bot.dispatch("tourney_registration_deny", message, RegDeny.duplicate, tourney)

            ctx = await self.bot.get_context(message)

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

            if tourney.success_message:
                self.bot.loop.create_task(send_success_message(ctx, tourney.success_message))

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

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not all((payload.guild_id, payload.member, not payload.member.bot)):
            return

        if not payload.channel_id in self.bot.tourney_channels:
            return

        tourney = await Tourney.get_or_none(registration_channel_id=payload.channel_id)

        if not tourney:
            return self.bot.tourney_channels.discard(payload.channel_id)

        if not str(payload.emoji) in tourney.emojis.values():
            return

        
    # @Cog.listener(name="on_message")
    # async def on_media_partner_message(self, message: discord.Message):
    #     if not all((message.guild, not message.author.bot, message in self.bot.media_partner_channels)):
    #         return

    #     tourney = await Tourney.get_or_none(media_partner_ids__contains=message.channel.id)

    #     if not tourney:
    #         return self.bot.media_partner_channels.discard(message.channel.id)

    #     if (modrole := tourney.modrole) and modrole in message.author.roles:
    #         return
