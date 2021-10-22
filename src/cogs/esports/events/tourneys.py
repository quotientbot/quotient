from __future__ import annotations
from contextlib import suppress

import typing

from models.esports.tourney import MediaPartner

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
    get_tourney_slots,
)
from unicodedata import normalize
from constants import EsportsLog, RegDeny

from tortoise.exceptions import DoesNotExist

import discord
import asyncio
import utils


class TourneyEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.__tourney_lock = asyncio.Lock()

    async def __process_tourney_message(self, message: discord.Message, tourney: Tourney, *, check_duplicate=True):
        """
        Processes a message that is a tourney message.

        :param check_duplicate: In case we want a message to be processed without these checks.
        """

        teamname = utils.find_team(message)

        try:
            await tourney.refresh_from_db()  # Refetch Tourney to check get its updated instance
        except DoesNotExist:
            return

        if not tourney or tourney.closed:  # Tourney is deleted or not opened.
            return

        if tourney.no_duplicate_name and check_duplicate:
            async for slot in tourney.assigned_slots.all():
                if slot.team_name == teamname:
                    return self.bot.dispatch("tourney_registration_deny", message, RegDeny.duplicate, tourney)

        ctx = await self.bot.get_context(message)

        assigned_slots = await tourney.assigned_slots.order_by("-num").first()

        numb = 0 if assigned_slots is None else assigned_slots.num

        slot = TMSlot(
            leader_id=ctx.author.id,
            team_name=teamname,
            num=numb + 1,
            members=[m.id for m in message.mentions],
            jump_url=message.jump_url,
            message_id=message.id,
        )

        await tourney.add_assigned_slot(slot,ctx.message)

        self.bot.loop.create_task(tourney.finalize_slot(ctx))

        self.bot.dispatch(
            "tourney_log",
            EsportsLog.success,
            tourney,
            message=ctx.message,
        )

        if tourney.total_slots <= await tourney.assigned_slots.all().count():
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

        if tourney.is_ignorable(message.author):
            return

        if not before_registrations(message, tourney.role):
            return await cannot_take_registration(message, tourney)

        message.content = normalize("NFKC", message.content.lower())

        if not await check_tourney_requirements(self.bot, message, tourney):
            return

        async with self.__tourney_lock:
            await self.__process_tourney_message(message, tourney)

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

        slot = await TMSlot.get_or_none(message_id=payload.message_id)

        e = str(payload.emoji)

        message = None
        with suppress(discord.HTTPException, AttributeError):
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

        if not message:
            return

        member = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, payload.user_id)

        if not slot and e == tourney.cross_emoji:
            return  # no need to do anything kyuki already registered nai hai user

        if not slot and e == tourney.check_emoji:
            if tourney.total_slots <= await tourney.assigned_slots.all().count():
                return await channel.send(f"{getattr(member, 'mention','')}, Slots are already full.", delete_after=6)

            # TODO:send log here
            return await self.__process_tourney_message(message, tourney, check_duplicate=False)

        if str(payload.emoji) == tourney.check_emoji:
            return

        if str(payload.emoji) == tourney.cross_emoji:
            return await ...  # cancel kardo slot user ka

    @Cog.listener(name="on_message")
    async def on_media_partner_message(self, message: discord.Message):
        if not all((message.guild, not message.author.bot, message in self.bot.media_partner_channels)):
            return

        media_partner = await MediaPartner.get_or_none(pk=message.channel.id)
        if not media_partner:
            return self.bot.media_partner_channels.discard(message.channel.id)

        tourney = await Tourney.get_or_none()

        if not tourney:
            return self.bot.media_partner_channels.discard(message.channel.id)

        if tourney.is_ignorable(message.author):
            return

        if not tourney.multiregister and message.author.id in get_tourney_slots(await tourney.assigned_slots.all()):
            self.bot.dispatch("tourney_registration_deny", message, RegDeny.multiregister, tourney)
            return await message.add_reaction(tourney.cross_emoji)

    @Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        message_id = payload.message_id
        await Tourney.filter(slotm_message_id=message_id).update(slotm_message_id=None, slotm_channel_id=None)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await Tourney.filter(slotm_channel_id=channel.id).update(slotm_channel_id=None, slotm_message_id=None)

    @Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles != after.roles:
            tourney = await Tourney.filter(guild_id=before.guild.id).first()
            if not tourney:
                return

            msg = None
            if role := tourney.modrole:
                if role in after.roles and not role in before.roles:
                    msg = (
                        f"Congratulations {before.mention} on becoming a {role.mention},\n\n"
                        "Here's a list of perks you get with the new responsibilities:\n"
                        "• You can now use all `qtourney` commands.\n"
                        "• You can now edit, manage or even delete any tourney.\n"
                        "• **Your messages are now ignored in all the registration channels.**\n\n"
                        "Good luck!"
                    )

                elif role in before.roles and not role in after.roles:
                    msg = (
                        f"{before.mention} is no longer a {role.mention},\n"
                        "All the special perks they enjoyed, are now revoked."
                    )

                if msg:
                    with suppress(discord.HTTPException, AttributeError):
                        await tourney.logschan.send(msg)
