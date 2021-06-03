from __future__ import annotations
import typing
from unicodedata import decomposition

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog, Context

from .utils import (
    toggle_channel,
    scrim_end_process,
    postpone_scrim,
    is_valid_scrim,
    tourney_end_process,
    cannot_take_registration,
    get_slots,
    get_tourney_slots,
)
from utils import (
    default,
    time,
    day_today,
    inputs,
    checks,
    FutureTime,
    human_timedelta,
    get_chunks,
)

from .converters import ScrimConverter, TourneyConverter
from constants import Day, IST
from discord.ext.commands.cooldowns import BucketType
from models import *

from datetime import timedelta, datetime
from discord import AllowedMentions
from discord.ext import commands

from .errors import ScrimError, SMError, TourneyError
from prettytable import PrettyTable

import discord
import asyncio
import config
from .menus import *
from typing import NamedTuple

QueueMessage = NamedTuple("QueueMessage", [("scrim", Scrim), ("message", discord.Message)])
TourneyQueueMessage = NamedTuple("TourneyQueueMessage", [("tourney", Tourney), ("message", discord.Message)])


class ScrimManager(Cog, name="Esports"):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.tourney_queue = asyncio.Queue()
        self.bot.loop.create_task(self.fill_registration_channels())
        self.bot.loop.create_task(self.registration_worker())
        self.bot.loop.create_task(self.tourney_registration_worker())

    async def cog_command_error(self, ctx, error):
        if isinstance(error, (ScrimError, TourneyError)):
            return await ctx.error(error)

    async def add_role_and_reaction(self, ctx, role):
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await ctx.author.add_roles(role)

    async def fill_registration_channels(self):
        records = Scrim.filter(opened_at__lte=datetime.now(tz=IST)).all()
        self.registration_channels = set()

        async for record in records:
            self.registration_channels.add(record.registration_channel_id)

        records = TagCheck.all()
        self.tagcheck_channels = set()

        async for record in records:
            self.tagcheck_channels.add(record.channel_id)

        records = Tourney.filter(started_at__not_isnull=True)
        self.tourney_channels = set()

        async for record in records:
            self.tourney_channels.add(record.registration_channel_id)

    async def registration_worker(self):
        while True:
            try:
                queue_message: QueueMessage = await self.queue.get()
                scrim, message = queue_message.scrim, queue_message.message

                ctx = await self.bot.get_context(message)

                teamname = default.find_team(message)

                scrim = await Scrim.get_or_none(pk=scrim.id)  # Refetch Scrim to check get its updated instance

                if not scrim or scrim.closed:  # Scrim is deleted or not opened yet.
                    continue

                try:
                    slot_num = scrim.available_slots[0]
                except:
                    continue  # this will never happen though

                slot = await AssignedSlot.create(
                    user_id=ctx.author.id,
                    team_name=teamname,
                    num=slot_num,
                    jump_url=message.jump_url,
                )

                await scrim.assigned_slots.add(slot)

                await Scrim.filter(pk=scrim.id).update(available_slots=ArrayRemove("available_slots", slot_num))
                self.bot.loop.create_task(self.add_role_and_reaction(ctx, scrim.role))

                role_given = True

                self.bot.dispatch(
                    "scrim_log",
                    "reg_success",
                    scrim,
                    message=ctx.message,
                    role_added=role_given,
                )

                if len(scrim.available_slots) == 1:
                    await scrim_end_process(ctx, scrim)

            except Exception:  # I know something's breaking the loop and I know no better way to find out.
                user = self.bot.get_user(548163406537162782)
                await user.send(Exception)
                continue

    async def tourney_registration_worker(self):
        while True:
            queue_message: TourneyQueueMessage = await self.tourney_queue.get()
            tourney, message = queue_message.tourney, queue_message.message

            ctx = await self.bot.get_context(message)

            teamname = default.find_team(message)

            tourney = await Tourney.get_or_none(pk=tourney.id)  # Refetch Tourney to check get its updated instance

            if not tourney or tourney.closed:  # Tourney is deleted or not opened.
                continue

            assigned_slots = await tourney.assigned_slots.order_by(
                "-id"
            ).first()  # we don't count them all instead we get num from last registration

            numb = 0 if assigned_slots is None else assigned_slots.num
            slot = await TMSlot.create(
                leader_id=ctx.author.id,
                team_name=teamname,
                num=numb + 1,
                members=[m.id for m in message.mentions],
                jump_url=message.jump_url,
            )

            await tourney.assigned_slots.add(slot)

            self.bot.loop.create_task(self.add_role_and_reaction(ctx, tourney.role))
            role_given = True

            self.bot.dispatch(
                "tourney_log",
                "reg_success",
                tourney,
                message=ctx.message,
                role_added=role_given,
                assigned_slot=slot,
                num=numb + 1,
            )

            if tourney.total_slots == numb + 1:
                await tourney_end_process(ctx, tourney)

    @property
    def reminders(self):
        return self.bot.get_cog("Reminders")

    # ************************************************************************************************

    @commands.Cog.listener()
    async def on_scrim_open_timer_complete(self, timer: Timer):
        """This listener opens the scrim registration at time."""
        scrim_id = timer.kwargs["scrim_id"]
        scrim = await Scrim.get_or_none(pk=scrim_id)

        if not scrim:  # we don't want to do anything if the scrim is deleted
            return

        if scrim.open_time != timer.expires:  # If time is not same return :)
            return

        if scrim.toggle != True or not Day(day_today()) in scrim.open_days:
            return await postpone_scrim(self.bot, scrim)

        guild = scrim.guild
        if not guild:
            return await scrim.delete()

        if not await is_valid_scrim(self.bot, scrim):
            return

        scrim_ping_role = scrim.ping_role

        reserved_count = await scrim.reserved_slots.all().count()

        embed = discord.Embed(
            color=discord.Color(config.COLOR),
            title="Registration is now open!",
            description=f"📣 **`{scrim.required_mentions}`** mentions required.\n"
            f"📣 Total slots: **`{scrim.total_slots}`** [`{reserved_count}` slots reserved]",
        )

        oldslots = await scrim.assigned_slots
        await AssignedSlot.filter(id__in=(slot.id for slot in oldslots)).delete()

        await scrim.assigned_slots.clear()

        # here we insert a list of slots we can give for the registration.
        # we insert only the empty slots not the reserved ones to avoid extra queries during creation of slots for reserved users.
        # await Scrim.filter(id=scrim.id).update(available_slots=await available_to_reserve(scrim))

        await self.bot.db.execute(
            """
            UPDATE public."sm.scrims" SET available_slots = $1 WHERE id = $2
            """,
            await available_to_reserve(scrim),
            scrim.id,
        )
        async for slot in scrim.reserved_slots.all():
            assinged_slot = await AssignedSlot.create(
                num=slot.num,
                user_id=slot.user_id,
                team_name=slot.team_name,
                jump_url=None,
            )

            await scrim.assigned_slots.add(assinged_slot)

            self.bot.loop.create_task(
                guild.get_member(slot.user_id).add_roles(scrim.role),
            )

        # Opening Channel for Normal Janta
        registration_channel = scrim.registration_channel
        open_role = scrim.open_role
        channel_update = await toggle_channel(registration_channel, open_role, True)

        self.registration_channels.add(registration_channel.id)

        await Scrim.filter(pk=scrim.id).update(
            open_time=scrim.open_time + timedelta(hours=24),
            opened_at=datetime.now(tz=IST),
            closed_at=None,
            slotlist_message_id=None,
        )

        await scrim.refresh_from_db(("open_time",))

        # Creating a new Reminder
        await self.reminders.create_timer(
            scrim.open_time,
            "scrim_open",
            scrim_id=scrim.id,
        )

        await registration_channel.send(
            content=getattr(scrim_ping_role, "mention", None),
            embed=embed,
            allowed_mentions=AllowedMentions(roles=True, everyone=True),
        )

        self.bot.dispatch("scrim_log", "open", scrim, permission_updated=channel_update)

    @commands.Cog.listener("on_message")
    async def on_tourney_registration(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id
        if channel_id not in self.tourney_channels:
            return

        tourney = await Tourney.get_or_none(registration_channel_id=channel_id)
        if tourney is None:
            return self.tourney_channels.discard(channel_id)

        if tourney.started_at is None:
            return

        if tourney.modrole in message.author.roles:
            return

        if (
            not message.guild.me.guild_permissions.manage_roles
            or tourney.role > message.guild.me.top_role
            or not message.channel.permissions_for(message.channel.guild.me).add_reactions
        ):
            return await cannot_take_registration(message, "tourney", tourney)

        if tourney.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):  # mentioned bots
            return self.bot.dispatch("tourney_registration_deny", message, "mentioned_bots", tourney)

        elif not len(message.mentions) >= tourney.required_mentions:
            return self.bot.dispatch("tourney_registration_deny", message, "insufficient_mentions", tourney)

        elif message.author.id in tourney.banned_users:
            return self.bot.dispatch("tourney_registration_deny", message, "banned", tourney)

        elif message.author.id in get_tourney_slots(await tourney.assigned_slots.all()) and not tourney.multiregister:
            return self.bot.dispatch("tourney_registration_deny", message, "multiregister", tourney)

        self.tourney_queue.put_nowait(TourneyQueueMessage(tourney, message))

    @commands.Cog.listener("on_message")
    async def on_scrim_registration(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel_id = message.channel.id

        if channel_id in self.tagcheck_channels:  # for the sake of cleanliness :c
            return self.bot.dispatch("tagcheck_message", message)

        if channel_id not in self.registration_channels:
            return

        scrim = await Scrim.get_or_none(
            registration_channel_id=channel_id,
        )

        if scrim is None:  # Scrim is possibly deleted
            return self.registration_channels.discard(channel_id)

        if scrim.opened_at is None:
            # Registration isn't opened yet.
            return

        if scrim.modrole in message.author.roles:
            return

        if (
            not message.guild.me.guild_permissions.manage_roles
            or scrim.role > message.guild.me.top_role
            or not message.channel.permissions_for(message.channel.guild.me).add_reactions
        ):
            return await cannot_take_registration(message, "scrim", scrim)

        if scrim.required_mentions and not all(map(lambda m: not m.bot, message.mentions)):  # mentioned bots
            return self.bot.dispatch("scrim_registration_deny", message, "mentioned_bots", scrim)

        elif not len(message.mentions) >= scrim.required_mentions:
            return self.bot.dispatch("scrim_registration_deny", message, "insufficient_mentions", scrim)

        elif message.author.id in await scrim.banned_user_ids():
            return self.bot.dispatch("scrim_registration_deny", message, "banned", scrim)

        elif message.author.id in get_slots(await scrim.assigned_slots.all()) and not scrim.multiregister:
            return self.bot.dispatch("scrim_registration_deny", message, "multiregister", scrim)

        self.queue.put_nowait(QueueMessage(scrim, message))

    # ************************************************************************************************

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if message.channel.id in self.registration_channels:
            scrim = await Scrim.get_or_none(registration_channel_id=message.channel.id)
            if not scrim or not scrim.opened_at:  # either scrim doesn't exist or it is closed.
                return

            if not message.author.id in (user.user_id for user in await scrim.assigned_slots.all()):
                return

            slot = [slot for slot in await scrim.assigned_slots.all() if slot.user_id == message.author.id]
            if not len(slot):  # means their registration was denied
                return
            else:
                slot = slot[0]

            self.bot.dispatch("scrim_registration_delete", scrim, message, slot)

    # ************************************************************************************************

    @commands.group(aliases=("s", "sm"), invoke_without_command=True)
    async def smanager(self, ctx):
        """
        Contains commands related to Quotient's powerful scrims manager.
        """
        await ctx.send_help(ctx.command)

    def config_embed(self, value, description: str):
        embed = discord.Embed(
            color=discord.Color(config.COLOR),
            title=f"🛠️ Scrims Manager ({value}/6)",
            description=description,
        )
        embed.set_footer(text=f'Reply with "cancel" to stop the process.')
        return embed

    # ************************************************************************************************

    @smanager.command(name="setup")
    @checks.can_use_sm()
    @checks.has_done_setup()
    @commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True)
    @commands.max_concurrency(1, BucketType.guild)
    async def s_setup(self, ctx: Context):
        """
        Setup Scrims Manager for a channel.
        Without premium you can setup scrims manager for upto 3 channels, however with Quotient Premium there isn't any limit.
        """

        count = await Scrim.filter(guild_id=ctx.guild.id).count()

        guild = await Guild.get(guild_id=ctx.guild.id)

        if count == 3 and not guild.is_premium:
            raise ScrimError(
                f"You need to upgrade to Quotient Premium to host more than 3 scrims.\n{self.bot.config.WEBSITE}/premium"
            )

        def check(message: discord.Message):
            if message.content.strip().lower() == "cancel":
                raise ScrimError("Alright, reverting all process.")

            return message.author == ctx.author and ctx.channel == message.channel

        # Registration Channel.
        scrim = Scrim(
            guild_id=ctx.guild.id,
            host_id=ctx.author.id,
        )
        await ctx.send(
            embed=self.config_embed(
                1,
                "Which is the default registration channel?",
            )
        )
        channel = await inputs.channel_input(ctx, check)

        if await Scrim.filter(registration_channel_id=channel.id).count():
            raise ScrimError("This channel is already a registration channel.")

        if not channel.permissions_for(ctx.me).manage_channels:
            raise ScrimError(f"I require `manage channels` permission in **{channel}**.")

        scrim.registration_channel_id = channel.id

        # Slotlist Channel
        await ctx.send(
            embed=self.config_embed(
                2,
                f"Which is default slotlist channel for {scrim.registration_channel.mention}?",
            )
        )

        channel = await inputs.channel_input(ctx, check)

        scrim.slotlist_channel_id = channel.id

        # Role (Registered Users)
        await ctx.send(
            embed=self.config_embed(
                3,
                f"What role should I give for correct registration?",
            )
        )

        role = await inputs.role_input(ctx, check)

        scrim.role_id = role.id

        # Mentions Limit

        await ctx.send(
            embed=self.config_embed(
                4,
                "How many mentions are required for successful registration?" " (Can't be more than 10 or less than 0.)",
            )
        )

        scrim.required_mentions = await inputs.integer_input(
            ctx,
            check,
            limits=(0, 10),
        )

        # Total Slots

        await ctx.send(
            embed=self.config_embed(
                5,
                "How many total slots are there? (Can't be more than 30 or less than 1.)",
            )
        )

        scrim.total_slots = await inputs.integer_input(
            ctx,
            check,
            limits=(1, 30),
        )

        await ctx.send(
            embed=self.config_embed(
                6,
                "**At what time should I open registrations?**"
                "\n> Time must be in 24h and in this format **`hh:mm`**\n"
                "**Example: 14:00** - Registration will open at 2PM.\n\n"
                "**Currently Quotient works according to Indian Standard Time (UTC+05:30)**",
            )
        )
        scrim.open_time = await inputs.time_input(ctx, check)

        registration_channel = scrim.registration_channel

        fields = (
            f"Registration Channel: {registration_channel.mention}",
            f"Slotlist Channel: {scrim.slotlist_channel.mention}",
            f"Role: {scrim.role.mention}",
            f"Minimum Mentions: {scrim.required_mentions}",
            f"Slots: {scrim.total_slots}",
            f"Open Time: {time(scrim.open_time)}",
        )

        title = "Are these correct?"
        description = "\n".join(f"`{idx}.` {field}" for idx, field in enumerate(fields, start=1))

        confirm = await ctx.prompt(description, title=title)
        if not confirm:
            await ctx.send("Ok, Aborting!")
        else:
            message = await ctx.send("Setting up everything!")
            reason = "Created for scrims management."

            # Scrims MODS
            scrims_mod = discord.utils.get(ctx.guild.roles, name="scrims-mod")

            if scrims_mod is None:
                scrims_mod = await ctx.guild.create_role(name="scrims-mod", color=0x00FFB3, reason=reason)

            overwrite = registration_channel.overwrites_for(ctx.guild.default_role)
            overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
            await registration_channel.set_permissions(scrims_mod, overwrite=overwrite)

            # Srims LOGS
            scrims_log_channel = discord.utils.get(ctx.guild.text_channels, name="quotient-scrims-logs")

            if scrims_log_channel is None:
                guild = ctx.guild
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    scrims_mod: discord.PermissionOverwrite(read_messages=True),
                }
                scrims_log_channel = await ctx.guild.create_text_channel(
                    name="quotient-scrims-logs",
                    overwrites=overwrites,
                    reason=reason,
                )

                # Sending Message to scrims-log-channel
                note = await scrims_log_channel.send(
                    embed=discord.Embed(
                        description=f"If events related to scrims i.e opening registrations or adding roles, "
                        f"etc are triggered, then they will be logged in this channel. "
                        f"Also I have created {scrims_mod.mention}, you can give that role to your "
                        f"scrims-moderators. User with {scrims_mod.mention} can also send messages in "
                        f"registration channels and they won't be considered as scrims-registration.\n\n"
                        f"`Note`: **Do not rename this channel.**",
                        color=discord.Color(config.COLOR),
                    )
                )
                await note.pin()

            await scrim.save()
            await self.reminders.create_timer(scrim.open_time, "scrim_open", scrim_id=scrim.id)
            text = f"Scrims Management Setup Complete. (`Scrims ID: {scrim.id}`)"
            try:
                await message.edit(content=text)
            except discord.NotFound:
                await ctx.send(text)

    # ************************************************************************************************

    @smanager.command(name="edit")
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    @checks.can_use_sm()
    async def s_edit(self, ctx, *, scrim: ScrimConverter):
        """
        Edit scrims manager config for a scrim.
        """
        menu = ConfigEditMenu(scrim=scrim)
        await menu.start(ctx)

    # ************************************************************************************************

    @smanager.command(name="days")
    @checks.can_use_sm()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_days(self, ctx, *, scrim: ScrimConverter):
        """
        Edit open days for a scrim.
        """
        menu = DaysMenu(scrim=scrim)
        await menu.start(ctx)

    # @smanager.command(name="open")
    # async def s_open(self, ctx, scrim_id: int):
    #     pass

    @smanager.command(name="close")
    @checks.can_use_sm()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True)
    async def s_close(self, ctx, scrim: ScrimConverter):
        """
        Close a scrim immediately, even if the slots aren't full.
        """
        if scrim.opened_at is None:
            return await ctx.error(f"Scrim `({scrim.id})` is already closed.")

        else:
            prompt = await ctx.prompt(f"Are you sure you want to close Scrim: `{scrim.id}`?")
            if prompt:
                await scrim_end_process(ctx, scrim)
                await ctx.message.add_reaction(emote.check)

            else:
                await ctx.success(f"Ok!")

    @smanager.command(name="config")
    @checks.can_use_sm()
    @commands.cooldown(5, 1, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_config(self, ctx):
        """
        Get config of all the scrims you have setup.
        """

        allscrims = await Scrim.filter(guild_id=ctx.guild.id).all()

        if not len(allscrims):
            return await ctx.send(
                f"You do not have any scrims setup on this server.\n\nKindly use `{ctx.prefix}smanager setup` to setup one."
            )

        to_paginate = []
        for idx, scrim in enumerate(allscrims, start=1):
            reg_channel = getattr(scrim.registration_channel, "mention", "`Channel Deleted!`")
            slot_channel = getattr(scrim.slotlist_channel, "mention", "`Channel Deleted!`")

            role = getattr(scrim.role, "mention", "`Role Deleted!`")
            open_time = (scrim.open_time).strftime("%I:%M %p")
            open_role = getattr(scrim.open_role, "mention", "`Role Deleted!`")
            ping_role = getattr(scrim.ping_role, "mention", "`Not Set!`")
            mystring = f"> Scrim ID: `{scrim.id}`\n> Name: `{scrim.name}`\n> Registration Channel: {reg_channel}\n> Slotlist Channel: {slot_channel}\n> Role: {role}\n> Mentions: `{scrim.required_mentions}`\n> Total Slots: `{scrim.total_slots}`\n> Open Time: `{open_time}`\n> Toggle: `{scrim.stoggle}`\n> Open Role: {open_role}\n> Ping Role: {ping_role}\n> Slotlist start from: {scrim.start_from}"

            to_paginate.append(f"**`<<<<<<-- {idx:02d}. -->>>>>>`**\n{mystring}\n")

        paginator = Pages(
            ctx, title="Total Scrims: {}".format(len(to_paginate)), entries=to_paginate, per_page=1, show_entry_count=True
        )

        await paginator.paginate()

    # ************************************************************************************************

    @smanager.command(name="toggle")
    @checks.can_use_sm()
    async def s_toggle(self, ctx, scrim: ScrimConverter, option: str = None):
        """
        Toggle on/off things for a scrim.
        """
        valid_opt = ("scrim", "ping", "openrole", "autoclean", "autoslotlist", "multiregister")
        display = ",".join(map(lambda s: f"`{s}`", valid_opt))
        display_msg = f"Valid options are:\n{display}\n\nUsage Example: `smanager toggle {scrim.id} scrim`"

        if not option or option.lower() not in valid_opt:
            return await ctx.send(display_msg)

        stoggle = scrim.stoggle
        ping = scrim.ping_role_id
        openrole = scrim.open_role_id
        autoclean = scrim.autoclean

        if option.lower() == "scrim":
            await Scrim.filter(pk=scrim.id).update(stoggle=not (stoggle))
            await ctx.success(f"Scrim is now {'OFF' if stoggle else 'ON'}")

        elif option.lower() == "ping":
            if ping is None:
                return await ctx.error(f"Ping Role is not set.")

            await Scrim.filter(pk=scrim.id).update(ping_role_id=None)
            await ctx.success(f"Ping Role turned OFF.")

        elif option.lower() == "openrole":
            if openrole is None:
                return await ctx.error(f"Open Role is not set.")

            await Scrim.filter(pk=scrim.id).update(open_role_id=None)
            await ctx.success(f"Open Role set to {ctx.guild.default_role.mention}")

        elif option.lower() == "autoclean":
            await Scrim.filter(pk=scrim.id).update(autoclean=not (autoclean))
            await ctx.success(f"Autoclean turned {'OFF' if autoclean else 'ON'}")

        elif option.lower() == "autoslotlist":
            await Scrim.filter(pk=scrim.id).update(autoslotlist=not (scrim.autoslotlist))
            await ctx.success(f"Autopost-slotlist turned {'OFF' if scrim.autoslotlist else 'ON'}!")

        elif option.lower() == "multiregister":
            await Scrim.filter(pk=scrim.id).update(multiregister=not (scrim.multiregister))
            await ctx.success(f"Multiple registerations turned {'OFF' if scrim.multiregister else 'ON'}!")

    # ************************************************************************************************
    @smanager.group(name="slotlist", invoke_without_command=True)
    async def s_slotlist(self, ctx):
        """
        Create/ Edit or Send a scrim slotlist.
        """
        await ctx.send_help(ctx.command)

    @s_slotlist.command(name="send")
    @checks.can_use_sm()
    async def s_slotlist_send(self, ctx, scrim: ScrimConverter):
        """
        Send a slotlist.
        """

        if not await scrim.teams_registered.count():
            return await ctx.error("Nobody registered yet!")

        else:
            embed, channel = await scrim.create_slotlist()
            await ctx.send(embed=embed)
            prompt = await ctx.prompt("This is how the slotlist looks. Should I send it?")
            if prompt:
                if channel is not None and channel.permissions_for(ctx.me).send_messages:
                    await channel.send(embed=embed)
                    await ctx.success(f"Slotlist sent successfully!")
                else:
                    await ctx.error(f"I can't send messages in {channel}")
            else:
                await ctx.success(f"Ok!")

    @s_slotlist.command(name="edit")
    @checks.can_use_sm()
    @commands.cooldown(5, 1, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_slotlist_edit(self, ctx, scrim: ScrimConverter):
        """
        Edit a slotlist
        """
        if not await scrim.teams_registered.count():
            return await ctx.error("Nobody registered yet!")

        menu = SlotEditor(scrim=scrim)
        await menu.start(ctx)

    @s_slotlist.command(name="format")
    @checks.can_use_sm()
    @commands.cooldown(5, 1, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_slotlist_format(self, ctx, scrim: ScrimConverter):
        """Set a default format for scrim slotlist."""
        menu = SlotlistFormatMenu(scrim=scrim)
        await menu.start(ctx)

    @s_slotlist.command(name="image")
    @checks.can_use_sm()
    @commands.cooldown(10, 1, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def s_slotlist_image(self, ctx, scrim: ScrimConverter):
        """
        Get image version of a slotlist.
        """
        if not await scrim.teams_registered.count():
            return await ctx.error("Nobody registered yet!")

        files = await scrim.create_slotlist_img()
        for file in files:
            await ctx.send(file=file)

    # ************************************************************************************************
    @smanager.command(name="delete")
    @checks.can_use_sm()
    async def s_delete(self, ctx, scrim: ScrimConverter):
        """
        Completely delete a scrim.
        """
        prompt = await ctx.prompt(
            f"Are you sure you want to delete scrim `{scrim.id}`?",
        )
        if prompt:
            self.registration_channels.discard(scrim.registration_channel_id)
            await scrim.delete()
            await ctx.success(f"Scrim (`{scrim.id}`) deleted successfully.")
        else:
            await ctx.success(f"Alright! Aborting")

    @smanager.command(name="ban")
    @checks.can_use_sm()
    async def s_ban(self, ctx, scrim: ScrimConverter, user: discord.Member, *, time: FutureTime = None):
        """
        Ban someone from the scrims temporarily or permanently.
        Time argument is optional.
        """
        if user.id in await scrim.banned_user_ids():
            return await ctx.send(
                f"**{str(user)}** is already banned from the scrims.\n\nUse `{ctx.prefix}smanager unban {scrim.id} {str(user)}` to unban them."
            )

        if time != None:

            expire_time = time.dt
        else:
            expire_time = None

        ban = await BannedTeam.create(user_id=user.id, expires=expire_time)
        await scrim.banned_teams.add(ban)

        if time != None:
            await self.reminders.create_timer(
                time.dt, "scrim_unban", scrim_id=scrim.id, user_id=user.id, banned_by=ctx.author.id
            )

            await ctx.success(
                f"**{str(user)}** has been successfully banned from Scrim (`{scrim.id}`) for **{human_timedelta(time.dt)}**"
            )
        else:
            await ctx.success(f"**{str(user)}** has been successfully banned from Scrim (`{scrim.id}`)")

    @smanager.command(name="unban")
    @checks.can_use_sm()
    async def s_unban(self, ctx, scrim: ScrimConverter, user: discord.Member):
        """
        Unban a banned team from a scrim.
        """
        if not user.id in await scrim.banned_user_ids():
            return await ctx.send(
                f"**{str(user)}** is not banned.\n\nUse `{ctx.prefix}smanager ban {str(user)}` to ban them."
            )

        ban = await scrim.banned_teams.filter(user_id=user.id).first()
        await BannedTeam.filter(id=ban.id).delete()
        await ctx.success(f"Successfully unbanned {str(user)} from Scrim (`{scrim.id}`)")

    @smanager.group(name="reserve", invoke_without_command=True)
    @commands.max_concurrency(1, BucketType.guild)
    async def s_reserve(self, ctx, scrim: ScrimConverter):
        """
        Add / Remove a team from the reserved list
        """
        menu = ReserveEditorMenu(scrim=scrim)
        await menu.start(ctx)

    @s_reserve.command(name="list", aliases=("all",))
    async def s_reverse_list(self, ctx, scrim: ScrimConverter):
        """
        Get a list of all reserved teams and their leaders.
        """
        if not sum(await scrim.reserved_user_ids()):
            return await ctx.error("None of the slots is reserved.")

        users = ""
        for idx, user in enumerate(await scrim.reserved_slots.all(), start=1):
            owner = ctx.guild.get_member(user.user_id) or self.bot.get_user(user.user_id)
            users += (
                f"`{idx:02d}`| {user.team_name.title()} ({getattr(owner,'mention','Not Found')}) [Slot: {user.num}]\n"
            )

        embed = discord.Embed(color=config.COLOR, description=users, title=f"Reserved Slots: {scrim.id}")
        await ctx.send(embed=embed)

    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************

    @commands.group(invoke_without_command=True, aliases=("tc",))
    async def tagcheck(self, ctx):
        """
        Setup tagcheck channel for scrims/tournaments.
        """
        await ctx.send_help(ctx.command)

    @tagcheck.command(name="set")
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_set(self, ctx, channel: discord.TextChannel, mentions=0):
        """
        Set a channel for tagcheck.
        2nd argument is required mentions, Its zero by default.
        """
        if not (channel.permissions_for(ctx.me).send_messages and channel.permissions_for(ctx.me).embed_links):
            return await ctx.error(f"I need `send_messages` and `embed_links` permissions in {channel.mention}")

        if channel.id in self.registration_channels:
            return await ctx.error("This is a scrims registration channel, Kindly choose a different channel.")
        count = await TagCheck.filter(guild_id=ctx.guild.id).count()
        if count:
            return await ctx.error(
                f"You already have a tagcheck channel.\n\nRemove it with :`{ctx.prefix}tagcheck remove`"
            )

        await TagCheck.create(guild_id=ctx.guild.id, channel_id=channel.id, required_mentions=mentions)
        self.tagcheck_channels.add(channel.id)
        await ctx.success(f"Successfully set **{channel}** as a tagcheck channel.")

    @tagcheck.command(name="config")
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_config(self, ctx):
        """
        Get tagcheck config.
        """
        check = await TagCheck.get_or_none(pk=ctx.guild.id)
        if not check:
            return await ctx.send(
                f"You don't have a tagcheck channel.\n\nDo it like: `{ctx.prefix}tagcheck set {ctx.channel}`"
            )

        channel = check.channel

        embed = discord.Embed(color=config.COLOR)
        embed.add_field(name="Channel", value=getattr(channel, "mention", "Channel Deleted!"))
        embed.add_field(name="Required Mentions", value=check.required_mentions)
        await ctx.send(embed=embed)

    @tagcheck.command(name="remove", aliases=("stop", "delete"))
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_remove(self, ctx):

        check = await TagCheck.get_or_none(pk=ctx.guild.id)
        if not check:
            return await ctx.send(
                f"You don't have a tagcheck channel.\n\nDo it like: `{ctx.prefix}tagcheck set {ctx.channel.mention}`"
            )

        self.tagcheck_channels.discard(check.channel_id)

        await check.delete()
        await ctx.success(f"Successfully removed the tagcheck channel.")

    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************

    def tcembed(self, value, description: str):
        embed = discord.Embed(
            color=discord.Color(config.COLOR),
            title=f"🛠️ Tournament Manager ({value}/5)",
            description=description,
        )
        embed.set_footer(text=f'Reply with "cancel" to stop the process.')
        return embed

    @commands.group(invoke_without_command=True, aliases=("tm", "t"))
    async def tourney(self, ctx):
        """Quotient's Awesome tournament commands"""
        await ctx.send_help(ctx.command)

    @tourney.command(name="create", aliases=("setup",))
    @checks.can_use_tm()
    @checks.has_done_setup()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True, manage_roles=True)
    async def t_create(self, ctx):
        """
        Create or setup tournaments
        """
        count = await Tourney.filter(guild_id=ctx.guild.id).count()
        guild = await Guild.get(guild_id=ctx.guild.id)
        if count == 2 and not guild.is_premium:
            raise TourneyError("You can't have more than 2 tournaments concurrently.")

        def check(message: discord.Message):
            if message.content.strip().lower() == "cancel":
                raise TourneyError("Alright, reverting all process.")

            return message.author == ctx.author and ctx.channel == message.channel

        tourney = Tourney(
            guild_id=ctx.guild.id,
            host_id=ctx.author.id,
        )
        await ctx.send(embed=self.tcembed(1, "Which is the default registeration channel?"))
        channel = await inputs.channel_input(ctx, check)

        if await Tourney.filter(registration_channel_id=channel.id).count():
            raise TourneyError(f"**{channel}** is already a registration channel.")

        if not channel.permissions_for(ctx.me).manage_channels:
            raise TourneyError(f"I require `manage channels` permission in **{channel}**.")

        tourney.registration_channel_id = channel.id

        await ctx.send(embed=self.tcembed(2, "Which is the confirmed teams channel?"))
        channel = await inputs.channel_input(ctx, check)

        tourney.confirm_channel_id = channel.id

        await ctx.send(
            embed=self.tcembed(
                3,
                f"What role should I give for correct registration?",
            )
        )

        role = await inputs.role_input(ctx, check)

        tourney.role_id = role.id

        # Mentions Limit

        await ctx.send(
            embed=self.tcembed(
                4,
                "How many mentions are required for successful registration?" " (Can't be more than 10 or less than 0.)",
            )
        )

        tourney.required_mentions = await inputs.integer_input(
            ctx,
            check,
            limits=(0, 10),
        )

        # Total Slots

        await ctx.send(
            embed=self.tcembed(
                5,
                "How many total slots are there? (Can't be more than 5000 or less than 1.)",
            )
        )

        tourney.total_slots = await inputs.integer_input(
            ctx,
            check,
            limits=(1, 5000),
        )

        fields = [
            f"Registration Channel: {tourney.registration_channel}",
            f"Slotlist Channel: {tourney.confirm_channel}",
            f"Role: {tourney.role}",
            f"Minimum Mentions: {tourney.required_mentions}",
            f"Slots: {tourney.total_slots}",
        ]

        title = "Are these correct?"
        description = "\n".join(f"`{idx}.` {field}" for idx, field in enumerate(fields, start=1))

        confirm = await ctx.prompt(description, title=title)
        if not confirm:
            await ctx.send("Ok, Aborting!")
        else:
            message = await ctx.send("Setting up everything!")
            reason = "Created for tournament management."

            # Tourney MODS
            tourney_mod = discord.utils.get(ctx.guild.roles, name="tourney-mod")

            if tourney_mod is None:
                tourney_mod = await ctx.guild.create_role(name="scrims-mod", color=0x00FFB3, reason=reason)

            overwrite = tourney.registration_channel.overwrites_for(ctx.guild.default_role)
            overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
            await tourney.registration_channel.set_permissions(tourney_mod, overwrite=overwrite)

            # Tourney LOGS
            tourney_log_channel = discord.utils.get(ctx.guild.text_channels, name="quotient-tourney-logs")

            if tourney_log_channel is None:
                guild = ctx.guild
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    tourney_mod: discord.PermissionOverwrite(read_messages=True),
                }
                scrims_log_channel = await ctx.guild.create_text_channel(
                    name="quotient-tourney-logs",
                    overwrites=overwrites,
                    reason=reason,
                )

                # Sending Message to tourney-log-channel
                note = await scrims_log_channel.send(
                    embed=discord.Embed(
                        description=f"If events related to tournament i.e opening registrations or adding roles, "
                        f"etc are triggered, then they will be logged in this channel. "
                        f"Also I have created {tourney_mod.mention}, you can give that role to your "
                        f"tourney-moderators. User with {tourney_mod.mention} can also send messages in "
                        f"registration channels and they won't be considered as tourney-registration.\n\n"
                        f"`Note`: **Do not rename this channel.**",
                        color=discord.Color(config.COLOR),
                    )
                )
                await note.pin()

            await tourney.save()
            text = f"Tourney Management Setup Complete. (`Tourney ID: {tourney.id}`)\nUse `{ctx.prefix}tourney start {tourney.id}` to start the tourney."
            try:
                await message.edit(content=text)
            except discord.NotFound:
                await ctx.send(text)

    @tourney.command(name="config")
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def tourney_config(self, ctx):
        """Get config of all running tourneys"""
        records = await Tourney.filter(guild_id=ctx.guild.id).all()
        if not len(records):
            raise TourneyError(
                f"You do not have any tourney setup on this server.\n\nKindly use `{ctx.prefix}tourney create` to create one."
            )

        to_paginate = []
        for idx, tourney in enumerate(records, start=1):
            reg_channel = getattr(tourney.registration_channel, "mention", "`Channel Deleted!`")
            slot_channel = getattr(tourney.confirm_channel, "mention", "`Channel Deleted!`")

            role = getattr(tourney.role, "mention", "`Role Deleted!`")
            open_role = getattr(tourney.open_role, "mention", "`Role Deleted!`")
            mystring = f"> Tourney ID: `{tourney.id}`\n> Name: `{tourney.name}`\n> Registration Channel: {reg_channel}\n> Confirm Channel: {slot_channel}\n> Role: {role}\n> Mentions: `{tourney.required_mentions}`\n> Total Slots: `{tourney.total_slots}`\n> Open Role: {open_role}\n> Status: {'Open' if tourney.started_at else 'Closed'}"

            to_paginate.append(f"**`<<<<<<-- {idx:02d}. -->>>>>>`**\n{mystring}\n")

        paginator = Pages(
            ctx,
            title="Total Tourney: {}".format(len(to_paginate)),
            entries=to_paginate,
            per_page=1,
            show_entry_count=True,
        )

        await paginator.paginate()

    @tourney.command(name="delete")
    @checks.can_use_tm()
    async def tourney_delete(self, ctx, tourney_id: TourneyConverter):
        """Delete a tournament"""
        tourney = tourney_id
        prompt = await ctx.prompt(
            f"Are you sure you want to delete tournament `{tourney.id}`?",
        )
        if prompt:
            self.tourney_channels.discard(tourney.registration_channel_id)
            await tourney.delete()
            await ctx.success(f"Tourney (`{tourney.id}`) deleted successfully.")
        else:
            await ctx.success(f"Alright! Aborting")

    @tourney.command(name="groups")
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def tourney_group(self, ctx, tourney: TourneyConverter, group_size: int = 20):
        """Get groups of the tournament."""
        records = await tourney.assigned_slots.all()
        if not len(records):
            raise TourneyError(f"There is no data to show as nobody registered yet!")

        m = await ctx.send(f"{emote.loading} | This may take some time. Please wait.")

        tables = []

        for record in get_chunks(records, group_size):
            x = PrettyTable()
            x.field_names = ["Slot", "Registered Posi.", "Team Name", "Leader"]
            for idx, i in enumerate(record, start=1):
                member = ctx.guild.get_member(i.leader_id)
                x.add_row([idx, i.num, i.team_name, str(member)])

            tables.append(str(x))

        await inputs.safe_delete(m)
        await ctx.send_file("\n\n\n\n\n".join(tables), name="slotlist.text")

    @tourney.command(name="data")
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def tourney_data(self, ctx, tourney: TourneyConverter):
        """Get all the data that Quotient collected for a tourney."""
        records = await tourney.assigned_slots.all()
        if not len(records):
            raise TourneyError(f"There is no data to show as nobody registered yet!")

        m = await ctx.send(f"{emote.loading} | This may take some time. Please wait.")

        y = PrettyTable()
        y.field_names = ["S No.", "Team Name", "Team Owner", "Teammates", " All Teammates in Server", "Jump URL"]

        for idx, record in enumerate(records, start=1):
            leader = str(ctx.guild.get_member(record.leader_id))

            if not len(record.members):
                teammates = "No Teammates!"
                all_here = "No team :("

            else:
                teamlist = tuple(map(ctx.guild.get_member, record.members))
                teammates = ", ".join(tuple(map(lambda x: str(x), teamlist)))
                all_here = ("No!", "Yes!")[all(teamlist)]

            y.add_row([idx, record.team_name, leader, teammates, all_here, record.jump_url])

        await inputs.safe_delete(m)
        await ctx.send_file(str(y), name="tourney_data.txt")

    @tourney.command(name="list", aliases=("all",))
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def tourney_list(self, ctx):
        """A list of all running tournaments."""
        records = await Tourney.filter(guild_id=ctx.guild.id).all()
        if not len(records):
            raise TourneyError(
                f"You do not have any tourney setup on this server.\n\nKindly use `{ctx.prefix}tourney create` to create one."
            )

        e = self.bot.embed(ctx)
        e.description = ""
        for count, i in enumerate(records, 1):
            channel = getattr(i.registration_channel, "mention", "`Deleted Channel!`")
            e.description += f"`{count}. ` | {channel} | Tourney ID: `{i.id}`"

        await ctx.send(embed=e)

    @tourney.command(name="rmslot", aliases=("deleteslot",))
    @checks.can_use_tm()
    async def tourney_deleteslot(self, ctx, tourney: TourneyConverter, *, user: discord.User):
        """Remove someone's slot"""
        slot = await tourney.assigned_slots.filter(leader_id=user.id).first()
        if not slot:
            raise TourneyError(f"**{user}** has no slot in Tourney (`{tourney.id}`)")

        prompt = await ctx.prompt(f"**{slot.team_name}** ({user.mention}) slot will be deleted.")
        if prompt:
            await TMSlot.filter(id=slot.id).delete()
            await ctx.success(f"Slot deleted!")

        else:
            await ctx.success(f"Ok!")

    @tourney.command(name="edit")
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def tourney_edit(self, ctx, tourney: TourneyConverter):
        """Edit a tournament's config."""

        menu = TourneyEditor(tourney=tourney)
        await menu.start(ctx)

    @tourney.command(name="start")
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True, manage_roles=True)
    async def tourney_start(self, ctx, tourney: TourneyConverter):
        """Start a tournament."""
        if tourney.started_at != None:
            raise TourneyError(f"Tourney (`{tourney.id}`)'s registration is already open.")

        channel = tourney.registration_channel
        open_role = tourney.open_role
        if channel is None:
            raise TourneyError(f"I cannot find tourney registration channel ({tourney.registration_channel_id})")

        elif not channel.permissions_for(ctx.me).manage_channels:
            raise TourneyError(f"I need `manage channels` permission in **{channel}**")

        elif open_role is None:
            raise TourneyError(f"I can not find open role for Tourney (`{tourney.id}`)")

        prompt = await ctx.prompt(f"Are you sure you want to start registrations for Tourney (`{tourney.id}`)?")
        if prompt:
            channel_update = await toggle_channel(channel, open_role, True)
            self.tourney_channels.add(channel.id)
            await Tourney.filter(pk=tourney.id).update(started_at=datetime.now(tz=IST), closed_at=None)
            await channel.send("**Registration is now Open!**")
            await ctx.message.add_reaction(emote.check)
        else:
            await ctx.success("OK!")

    @tourney.command(name="stop", aliases=("pause",))
    @checks.can_use_tm()
    @commands.bot_has_permissions(embed_links=True, manage_channels=True, manage_roles=True)
    async def tourney_stop(self, ctx, tourney: TourneyConverter):
        """Stop / Pause a tournament."""
        if tourney.closed_at != None:
            raise TourneyError(f"Tourney (`{tourney.id}`)'s registration is already closed.")

        channel = tourney.registration_channel
        open_role = tourney.open_role
        if channel is None:
            raise TourneyError(f"I cannot find tourney registration channel ({tourney.registration_channel_id})")

        elif not channel.permissions_for(ctx.me).manage_channels:
            raise TourneyError(f"I need `manage channels` permission in **{channel}**")

        elif open_role is None:
            raise TourneyError(f"I can not find open role for Tourney (`{tourney.id}`)")

        prompt = await ctx.prompt(
            f"Are you sure you want to stop registrations for Tourney (`{tourney.id}`)?\n>You can start them later with `{ctx.prefix}tourney start {tourney.id}` command"
        )
        if prompt:
            await toggle_channel(channel, open_role, False)
            await channel.send(f"Registration is now closed.")
            await Tourney.filter(pk=tourney.id).update(started_at=None, closed_at=datetime.now(tz=IST))
            await ctx.message.add_reaction(emote.check)
        else:
            await ctx.success("OK!")

    @tourney.command(name="ban")
    @checks.can_use_tm()
    async def tourney_ban(self, ctx, tourney: TourneyConverter, user: discord.User):
        """Ban someone from the tournament"""
        if user.id in tourney.banned_users:
            return await ctx.send(
                f"**{str(user)}** is already banned from the tourney.\n\nUse `{ctx.prefix}tourney unban {tourney.id} {user}` to unban them."
            )

        await Tourney.filter(pk=tourney.id).update(banned_users=ArrayAppend("banned_users", user.id))
        await ctx.success(f"**{str(user)}** has been successfully banned from Tourney (`{tourney.id}`)")

    @tourney.command(name="unban")
    @checks.can_use_tm()
    async def tourney_unban(self, ctx, tourney: TourneyConverter, user: discord.User):
        """Unban a banned user from tournament."""
        if user.id not in tourney.banned_users:
            return await ctx.send(
                f"**{str(user)}** is not banned the tourney.\n\nUse `{ctx.prefix}tourney ban {tourney.id} {user}` to ban them."
            )

        await Tourney.filter(pk=tourney.id).update(banned_users=ArrayRemove("banned_users", user.id))
        await ctx.success(f"**{str(user)}** has been successfully unbanned from Tourney (`{tourney.id}`)")

    @commands.command()
    async def format(self, ctx, *, registration_form):
        """Get your reg-format in a reusable form."""
        await ctx.send(f"```{registration_form}```")


def setup(bot):
    bot.add_cog(ScrimManager(bot))
    bot.add_cog(SMError(bot))
