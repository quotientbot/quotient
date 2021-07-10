from models import EasyTag, TagCheck, Scrim, Tourney, AssignedSlot, ArrayRemove, TMSlot, Timer
from core import Quotient, Cog, commands
from models.esports import SSVerify, SSData
from utils import emote, plural
from .utils import (
    available_to_reserve,
    check_scrim_requirements,
    delete_denied_message,
    purge_channel,
    purge_role,
    scrim_end_process,
    add_role_and_reaction,
    scrim_work_role,
    should_open_scrim,
    toggle_channel,
    tourney_end_process,
    before_registrations,
    cannot_take_registration,
    check_tourney_requirements,
    registration_open_embed,
)
from constants import AutocleanType, Day, EsportsLog, EsportsRole, SSStatus, IST, VerifyImageError
from .converters import EasyMemberConverter
from unicodedata import normalize
from contextlib import suppress
import discord, asyncio
import utils, json
import re

from config import IPC_BASE
from discord.ext import tasks
from typing import NamedTuple
from datetime import datetime, timedelta

QueueMessage = NamedTuple("QueueMessage", [("scrim", Scrim), ("message", discord.Message)])
TourneyQueueMessage = NamedTuple("TourneyQueueMessage", [("tourney", Tourney), ("message", discord.Message)])


class ScrimEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.scrim_queue = asyncio.Queue()
        self.tourney_queue = asyncio.Queue()
        self.scrim_registration_worker.start()
        self.tourney_registration_worker.start()

    def cog_unload(self):
        self.scrim_registration_worker.stop()
        self.tourney_registration_worker.stop()

    @tasks.loop(seconds=2, reconnect=True)
    async def scrim_registration_worker(self):
        while not self.scrim_queue.empty():
            queue_message: QueueMessage = await self.scrim_queue.get()
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
                user_id=ctx.author.id, team_name=teamname, num=slot_num, jump_url=message.jump_url, message_id=message.id
            )

            await scrim.assigned_slots.add(slot)

            await Scrim.filter(pk=scrim.id).update(available_slots=ArrayRemove("available_slots", slot_num))
            self.bot.loop.create_task(add_role_and_reaction(ctx, scrim.role))

            self.bot.dispatch("scrim_log", EsportsLog.success, scrim, message=ctx.message)

            if len(scrim.available_slots) == 1:
                await scrim_end_process(ctx, scrim)

    # ==========================================================================================================
    # ==========================================================================================================

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
            return await cannot_take_registration(message, tourney)

        message.content = normalize("NFKC", message.content.lower())

        if not await check_tourney_requirements(self.bot, message, tourney):
            return

        if not self.tourney_registration_worker.next_iteration or self.tourney_registration_worker.failed():
            # if for any fking reason its stopped , we want it to start again
            self.tourney_registration_worker.start()

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
            return await cannot_take_registration(message, scrim)

        message.content = normalize("NFKC", message.content.lower())

        if not await check_scrim_requirements(self.bot, message, scrim):
            return

        if not self.scrim_registration_worker.next_iteration or self.scrim_registration_worker.failed():
            # if for any fking reason its stopped , we want it to start again
            self.scrim_registration_worker.start()

        self.scrim_queue.put_nowait(QueueMessage(scrim, message))

    # ==========================================================================================================
    # ==========================================================================================================

    @Cog.listener()
    async def on_scrim_open_timer_complete(self, timer: Timer):
        """This listener opens the scrim registration at time."""

        scrim_id = timer.kwargs["scrim_id"]
        scrim = await Scrim.get_or_none(pk=scrim_id)

        if not scrim:  # we don't want to do anything if the scrim is deleted
            return

        if scrim.open_time != timer.expires:  # If time is not same return :)
            return

        await Scrim.filter(pk=scrim.id).update(
            open_time=scrim.open_time + timedelta(hours=24),
        )

        await self.bot.reminders.create_timer(
            scrim.open_time + timedelta(hours=24),
            "scrim_open",
            scrim_id=scrim.id,
        )  # we don't want to risk this

        if scrim.toggle != True or not Day(utils.day_today()) in scrim.open_days:
            return

        if scrim.opened_at and scrim.opened_at.strftime("%d-%b-%Y %I:%M %p") == datetime.now(tz=IST).strftime(
            "%d-%b-%Y %I:%M %p"
        ):
            return  # means we are having multiple timers for a single scrims :c shit

        guild = scrim.guild

        if not guild:
            return await scrim.delete()

        if not await should_open_scrim(scrim):
            return

        # reserved_count = await scrim.reserved_slots.all().count()

        # embed = discord.Embed(
        #     color=self.bot.color,
        #     title="Registration is now open!",
        #     description=f"📣 **`{scrim.required_mentions}`** mentions required.\n"
        #     f"📣 Total slots: **`{scrim.total_slots}`** [`{reserved_count}` slots reserved]",
        # )

        oldslots = await scrim.assigned_slots
        await AssignedSlot.filter(id__in=(slot.id for slot in oldslots)).delete()

        await scrim.assigned_slots.clear()

        # here we insert a list of slots we can give for the registration.
        # we insert only the empty slots not the reserved ones to avoid extra queries during creation of slots for reserved users.

        await self.bot.db.execute(
            """
            UPDATE public."sm.scrims" SET available_slots = $1 WHERE id = $2
            """,
            await available_to_reserve(scrim),
            scrim.id,
        )

        scrim_role = scrim.role
        async for slot in scrim.reserved_slots.all():
            assinged_slot = await AssignedSlot.create(
                num=slot.num,
                user_id=slot.user_id,
                team_name=slot.team_name,
                jump_url=None,
            )

            await scrim.assigned_slots.add(assinged_slot)

            with suppress(AttributeError):
                self.bot.loop.create_task(guild.get_member(slot.user_id).add_roles(scrim_role))

        # Opening Channel for Normal Janta
        registration_channel = scrim.registration_channel
        open_role = scrim.open_role

        await registration_channel.send(
            content=scrim_work_role(scrim, EsportsRole.ping),
            embed=await registration_open_embed(scrim),
            allowed_mentions=discord.AllowedMentions(roles=True, everyone=True),
        )

        channel_update = await toggle_channel(registration_channel, open_role, True)

        self.bot.scrim_channels.add(registration_channel.id)

        await Scrim.filter(pk=scrim.id).update(
            opened_at=datetime.now(tz=IST),
            closed_at=None,
            slotlist_message_id=None,
        )

        self.bot.dispatch("scrim_log", EsportsLog.open, scrim)

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
                    f"You need to mention `{utils.plural(tagcheck.required_mentions):teammate|teammates}`.",
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

    @Cog.listener()
    async def on_autoclean_timer_complete(self, timer: Timer):
        scrim_id = timer.kwargs["scrim_id"]

        scrim = await Scrim.get_or_none(pk=scrim_id)

        if not scrim:
            return

        if timer.expires != scrim.autoclean_time:
            return

        await Scrim.filter(pk=scrim.id).update(autoclean_time=scrim.autoclean_time + timedelta(hours=24))
        await self.bot.reminders.create_timer(scrim.autoclean_time + timedelta(hours=24), "autoclean", scrim_id=scrim.id)

        if AutocleanType.channel in scrim.autoclean:
            self.bot.loop.create_task(purge_channel(scrim.registration_channel))

            with suppress(discord.Forbidden, AttributeError):
                await scrim.logschan.send(
                    embed=discord.Embed(
                        color=discord.Color.green(),
                        description=f"{emote.check} | Channel Purge (Scrims Autoclean) executed successfully: {scrim.id}",
                    )
                )

        if AutocleanType.role in scrim.autoclean:
            self.bot.loop.create_task(purge_role(scrim.role))

            with suppress(discord.Forbidden, AttributeError):
                await scrim.logschan.send(
                    embed=discord.Embed(
                        color=discord.Color.green(),
                        description=f"{emote.check} | Role Purge (Scrims Autoclean) executed successfully: {scrim.id}",
                    )
                )

    # ==========================================================================================================

    @Cog.listener()
    async def on_ssverify_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if not message.channel.id in self.bot.ssverify_channels:
            return

        verify = await SSVerify.get_or_none(msg_channel_id=message.channel.id)

        if not verify:
            return self.bot.ssverify_channels.discard(message.channel.id)

        modrole = verify.modrole
        delete_after = verify.delete_after

        if modrole and modrole in message.author.roles:
            return

        records = await verify.data.filter(author_id=message.author.id)
        approved = sum(1 for i in records if i.status == SSStatus.approved)
        disapproved = sum(1 for i in records if i.status == SSStatus.disapproved)

        if approved >= verify.required_ss:
            return await message.reply(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=(
                        f"Your entry has already been confirmed, You don't need post more screenshots/messages here.\n"
                        f"{'**Message:** '+verify.success_message}"
                    ),
                    delete_after=delete_after,
                )
            )

        else:
            attachments = [i for i in message.attachments if i.content_type in ("image/png", "image/jpeg", "image/jpg")]
            if not attachments:
                return await message.reply(
                    embed=discord.Embed(
                        color=discord.Color.red(),
                        description=(
                            f"Kindly send a valid screenshot {verify.ss_type.value} to send for verification.\n"
                            "**Your history:**\n"
                            f"\n- `{approved}` approved screenshots."
                            f"\n- `{disapproved}` disapproved screenshots."
                            f"\n\nYou need a total of {verify.required_ss} approved screenshots."
                        ),
                    ),
                    delete_after=delete_after,
                )

            else:
                url = IPC_BASE + "/image/verify"
                headers = {"Content-Type": "application/json"}

                for attachment in attachments:
                    payload = json.dumps(
                        {"type": verify.ss_type.name, "name": verify.channel_name, "url": attachment.proxy_url}
                    )

                    res = await self.bot.session.get(url=url, headers=headers, data=payload)

                    if not res.get("ok"):
                        status = SSStatus.approved
                        _error = res.get("error")
                        if VerifyImageError(_error) == VerifyImageError.Invalid:
                            return await message.reply(
                                f"This doesn't seem to be a valid screenshot.\n"
                                "\nYou need a screenshot of the following account:\n"
                                f"<{verify.channel_link}>"
                            )

                        elif VerifyImageError(_error) == VerifyImageError.NotSame:
                            return await message.reply(
                                f"This screenshot doesn't belong to **{verify.channel_name}**\n\n"
                                "You need a screenshot of the following account:\n"
                                f"<{verify.channel_link}>"
                            )

                    else:
                        status = SSStatus.approved

                    slot = await SSData.create(
                        author_id=message.author.id,
                        channel_id=message.channel.id,
                        message_id=message.id,
                        image={
                            "name": attachment.filename,
                        },
                        status=status,
                    )
                    await verify.add(slot)

                records = await verify.data.filter(author_id=message.author.id)
                approved = sum(1 for i in records if i.status == SSStatus.approved)
                disapproved = sum(1 for i in records if i.status == SSStatus.disapproved)

                if approved >= verify.required_ss:
                    return await message.reply(
                        embed=discord.Embed(
                            color=discord.Color.red(),
                            description=(
                                f"Your entry has been confirmed, You don't need to post more screenshots/messages here.\n"
                                f"{'**Message:** '+verify.success_message}"
                            ),
                            delete_after=delete_after,
                        )
                    )
