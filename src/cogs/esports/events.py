from models import EasyTag, TagCheck, Scrim, Tourney, AssignedSlot, ArrayRemove, TMSlot
from core import Quotient, Cog
from .utils import (
    check_scrim_requirements,
    delete_denied_message,
    scrim_end_process,
    add_role_and_reaction,
    tourney_end_process,
    before_registrations,
    cannot_take_registration,
    check_tourney_requirements,
)
from .converters import EasyMemberConverter
from unicodedata import normalize
from contextlib import suppress
import discord, asyncio
import constants
import utils
import re

from typing import NamedTuple

QueueMessage = NamedTuple("QueueMessage", [("scrim", Scrim), ("message", discord.Message)])
TourneyQueueMessage = NamedTuple("TourneyQueueMessage", [("tourney", Tourney), ("message", discord.Message)])


class ScrimEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.scrim_queue = asyncio.Queue()
        self.tourney_queue = asyncio.Queue()
        self.bot.loop.create_task(self.scrim_registration_worker())
        self.bot.loop.create_task(self.tourney_registration_worker())

    def cog_unload(self):
        self.scrim_registration_worker.cancel()
        self.tourney_registration_worker.cancel()

    async def scrim_registration_worker(self):
        while True:
            queue_message: QueueMessage = await self.queue.get()
            scrim, message = queue_message.scrim, queue_message.message
            ctx = await self.bot.get_context(message)

            teamname = utils.find_team(message)

            scrim = await Scrim.get_or_none(pk=scrim.id)

            if not scrim or scrim.closed:  # Scrim is deleted or not opened yet.
                continue

            try:
                slot_num = scrim.available_slots[0]
            except IndexError:
                continue

            slot = await AssignedSlot.create(
                user_id=ctx.author.id,
                team_name=teamname,
                num=slot_num,
                jump_url=message.jump_url,
            )

            await scrim.assigned_slots.add(slot)

            await Scrim.filter(pk=scrim.id).update(available_slots=ArrayRemove("available_slots", slot_num))
            self.bot.loop.create_task(add_role_and_reaction(ctx, scrim.role))

            self.bot.dispatch("scrim_log", "reg_success", scrim, message=ctx.message)

            if len(scrim.available_slots) == 1:
                await scrim_end_process(ctx, scrim)

    # ==========================================================================================================
    # ==========================================================================================================

    async def tourney_registration_worker(self):
        while True:
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
                "reg_success",
                tourney,
                message=ctx.message,
                assigned_slot=slot,
                num=numb + 1,
            )

            if tourney.total_slots == numb + 1:
                await tourney_end_process(ctx, tourney)

    # ==========================================================================================================
    # ==========================================================================================================

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

        if modrole != None and modrole in message.author.roles:
            return

        if not before_registrations(message, tourney.role):
            return await cannot_take_registration(message, constants.EsportsType.tourney, tourney)

        if not await check_tourney_requirements(self.bot, message, tourney):
            return

        message.content = normalize("NFKC", message.content.lower())

        self.tourney_queue.put_nowait(TourneyQueueMessage(tourney, message))

    # ==========================================================================================================
    # ==========================================================================================================

    @Cog.listener("on_message")
    async def on_scrim_registration(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        if channel_id not in self.bot.scrim_channels:
            return

        scrim = await Scrim.get_or_none(
            registration_channel_id=channel_id,
        )

        if scrim is None:  # Scrim is possibly deleted
            return self.bot.scrim_channels.discard(channel_id)

        scrim_role = scrim.role
        modrole = scrim.modrole

        if scrim.opened_at is None or scrim_role is None:
            return

        if modrole and modrole in message.author.roles:
            return

        if not before_registrations(message, scrim_role):
            return await cannot_take_registration(message, constants.EsportsType.tourney, scrim)

        message.content = normalize("NFKC", message.content.lower())

        if not await check_scrim_requirements(self.bot, message, scrim):
            return

        self.queue.put_nowait(QueueMessage(scrim, message))

    # ==========================================================================================================
    # ==========================================================================================================

    @Cog.listener(name="on_message")
    async def on_tagcheck_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        if not channel_id in self.bot.tagcheck:
            return

        tagcheck = await TagCheck.get_or_none(channel_id=channel_id)

        if not tagcheck:
            return self.bot.tagcheck.discard(channel_id)

        ignore_role = tagcheck.ignorerole

        if ignore_role != None and ignore_role in message.author.roles:
            return

        with suppress(discord.Forbidden, discord.NotFound):
            ctx = await self.bot.get_context(message)

            _react = True
            if tagcheck.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):
                _react = False
                await message.reply("Kindly mention your real teammate.", delete_after=5)

            if not len(message.mentions) >= tagcheck.required_mentions:
                _react = False
                await message.reply(
                    f"You need to mention {utils.plural(tagcheck.required_mentions):teammate|teammates}`.",
                    delete_after=5,
                )

            team_name = utils.find_team(message)
            await message.add_reaction(("❌", "✅")[_react])

            if _react:
                embed = self.bot.embed(ctx)
                embed.description = f"Team Name: {team_name}\nPlayer(s): {(', '.join(m.mention for m in message.mentions)) if message.mentions else message.author.mention}"
                await message.reply(embed=embed)

            if tagcheck.delete_after and not _react:
                self.bot.loop.create_task(delete_denied_message(message, 15))

    # ==========================================================================================================
    # ==========================================================================================================

    @Cog.listener(name="on_message")
    async def on_eztag_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if not message.channel.id in self.bot.eztagchannels:
            return

        channel_id = message.channel.id
        eztag = await EasyTag.get_or_none(channel_id=channel_id)

        if not eztag:
            return self.bot.eztagchannels.discard(channel_id)

        ignore_role = eztag.ignorerole

        if ignore_role != None and ignore_role in message.author.roles:
            return

        with suppress(discord.Forbidden, discord.NotFound):
            ctx = await self.bot.get_context(message)

            tags = set(re.findall(r"\b\d{18}\b|\b@\w+", message.content, re.IGNORECASE))

            if not len(tags):
                await message.add_reaction("❌")
                return await ctx.reply(
                    "I couldn't find any discord tag in this form.\nYou can write your teammate's id , @their_name or @their_full_discord_tag",
                    delete_after=10,
                )

            members = list()
            for m in tags:
                members.append(await EasyMemberConverter().convert(ctx, m))

            mentions = ", ".join(members)

            msg = await ctx.reply(f"```{message.clean_content}\nDiscord Tags: {mentions}```")

            if eztag.delete_after:
                self.bot.loop.create_task(delete_denied_message(message, 60))
                self.bot.loop.create_task(delete_denied_message(msg, 60))

    # ==========================================================================================================
