from .utils import (
    toggle_channel,
    scrim_end_process,
    postpone_scrim,
    is_valid_scrim,
)
from discord.ext.commands.cooldowns import BucketType
from models import *
from utils import default, time, day_today
from datetime import timedelta, datetime
from utils.constants import IST, Day
from discord import AllowedMentions
from discord.ext import commands

from .errors import ScrimError, SMError
from utils import inputs, checks
from core import Cog

import discord
import asyncio
import config
from .menus import *
from typing import NamedTuple

# TODO: a seprate class to check scrim_id in cmd args

QueueMessage = NamedTuple("QueueMessage", [("scrim", Scrim), ("message", discord.Message)])


class ScrimManager(Cog, name="Esports"):
    def __init__(self, bot):
        self.bot = bot
        self.queue = asyncio.Queue()
        self.bot.loop.create_task(self.fill_registration_channels())
        self.bot.loop.create_task(self.registration_worker())

    async def fill_registration_channels(self):
        records = Scrim.filter(opened_at__lte=datetime.now(tz=IST)).all()
        self.registration_channels = set()

        async for record in records:
            self.registration_channels.add(record.registration_channel_id)

    async def registration_worker(self):
        while True:
            queue_message: QueueMessage = await self.queue.get()
            scrim, message = queue_message.scrim, queue_message.message

            ctx = await self.bot.get_context(message)

            teamname = default.find_team(message)

            scrim = await Scrim.get_or_none(pk=scrim.id)  # Refetch Scrim to check get its updated instancepass

            if not scrim or scrim.closed:  # Scrim is deleted or not opened yet.
                continue

            assigned_slots = await scrim.assigned_slots.all().count()

            slot = await AssignedSlot.create(
                user_id=ctx.author.id,
                team_name=teamname,
                num=assigned_slots + 1,
                jump_url=message.jump_url,
            )

            await scrim.assigned_slots.add(slot)

            await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            try:
                await ctx.author.add_roles(scrim.role)
                role_given = True
            except:
                role_given = False

            self.bot.dispatch(
                "scrim_log",
                "reg_success",
                scrim,
                message=ctx.message,
                role_added=role_given,
            )

            if scrim.total_slots == assigned_slots + 1:
                await scrim_end_process(ctx, scrim)

    @property
    def reminders(self):
        return self.bot.get_cog("Reminders")

    # ************************************************************************************************

    @commands.Cog.listener()
    async def on_scrim_open_timer_complete(self, timer: Timer):
        """This listener opens the scrim registration at time."""
        scrim_id = timer.kwargs["scrim_id"]
        scrim = await Scrim.get(pk=scrim_id)

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

        async for slot in scrim.reserved_slots.all():
            count = await scrim.assinged_slots.all().count()

            assinged_slot = AssignedSlot.create(
                user_id=slot.user_id,
                team_name=slot.team_name,
                jump_url=None,
                num=count + 1,
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
    async def on_scrim_registration(self, message: discord.Message):
        # if not message.guild or message.author.bot:
        #     return
        if message.author == self.bot.user:
            return

        channel_id = message.channel.id

        if channel_id not in self.registration_channels:
            return

        scrim = await Scrim.get_or_none(
            registration_channel_id=channel_id,
        )

        if scrim is None:  # Scrim is possibly deleted
            self.registration_channels.pop(channel_id)
            return

        if scrim.opened_at is None:
            # Registration isn't opened yet.
            return

        # if scrim.required_mentions and not all(
        #     map(lambda m: not m.bot, message.mentions)
        # ):  # mentioned bots
        #     return self.bot.dispatch(
        #         "scrim_registration_deny", message, "mentioned_bots", scrim
        #     )

        elif not len(message.mentions) >= scrim.required_mentions:
            return self.bot.dispatch("scrim_registration_deny", message, "insufficient_mentions", scrim)

        elif message.author.id in scrim.banned_users_ids:
            return self.bot.dispatch("scrim_registration_deny", message, "banned", scrim)

        self.queue.put_nowait(QueueMessage(scrim, message))

    # ************************************************************************************************

    @commands.group(aliases=("s",), invoke_without_command=True)
    async def smanager(self, ctx):
        await ctx.send_help(ctx.command)

    async def cog_command_error(self, ctx, error):
        if isinstance(error, ScrimError):
            return await ctx.send(error)

        raise error

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
    @commands.max_concurrency(1, BucketType.guild)
    async def s_setup(self, ctx):

        count = await Scrim.filter(guild_id=ctx.guild.id).count()

        if count > 3:
            raise ScrimError("You can't host more than 3 scrims concurrently.")

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

        fields = [
            f"Registration Channel: {registration_channel.mention}",
            f"Slotlist Channel: {scrim.slotlist_channel.mention}",
            f"Role: {scrim.role.mention}",
            f"Minimum Mentions: {scrim.required_mentions}",
            f"Slots: {scrim.total_slots}",
            f"Open Time: {time(scrim.open_time)}",
        ]

        title = "Are these correct?"
        description = "\n".join(f"`{idx}.` {field}" for idx, field in enumerate(fields, start=1))

        confirm = await ctx.prompt(description, title=title)
        confirm = True
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
    @checks.can_use_sm()
    async def s_edit(self, ctx, *, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")
        menu = ConfigEditMenu(scrim=scrim)
        await menu.start(ctx)

    # ************************************************************************************************

    @smanager.command(name="days")
    @checks.can_use_sm()
    async def s_days(self, ctx, *, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")
        menu = DaysMenu(scrim=scrim)
        await menu.start(ctx)

    # @smanager.command(name="open")
    # async def s_open(self, ctx, scrim_id: int):
    #     pass

    @smanager.command(name="close")
    @checks.can_use_sm()
    async def s_close(self, ctx, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")

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
    async def s_config(self, ctx):
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
            mystring = f"> Scrim ID: `{scrim.id}`\n> Name: `{scrim.name}`\n> Registration Channel: {reg_channel}\n> Slotlist Channel: {slot_channel}\n> Role: {role}\n> Mentions: `{scrim.required_mentions}`\n> Total Slots: `{scrim.total_slots}`\n> Open Time: `{open_time}`\n> Toggle: `{scrim.stoggle}`\n> Open Role: {open_role}\n> Ping Role: {ping_role}"

            to_paginate.append(f"**`<<<<<<-- {idx:02d}. -->>>>>>`**\n{mystring}\n")

        paginator = Pages(
            ctx, title="Total Scrims: {}".format(len(to_paginate)), entries=to_paginate, per_page=1, show_entry_count=True
        )

        await paginator.paginate()

    # ************************************************************************************************

    @smanager.command(name="toggle")
    @checks.can_use_sm()
    async def s_toggle(self, ctx, scrim_id: int, option: str = None):

        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")

        valid_opt = ("scrim", "ping", "openrole", "autoclean")
        display = ",".join(map(lambda s: f"`{s}`", valid_opt))
        display_msg = f"Valid options are:\n{display}\n\nUsage Example: `smanager toggle {scrim_id} scrim`"

        if not option or option.lower() not in valid_opt:
            return await ctx.send(display_msg)

    # ************************************************************************************************
    @smanager.group(name="slotlist", invoke_without_command=True)
    async def s_slotlist(self, ctx):
        await ctx.send_help(ctx.command)

    @s_slotlist.command(name="send")
    @checks.can_use_sm()
    async def s_slotlist_send(self, ctx, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")

        if not len(await scrim.teams_registered):
            return await ctx.error("Nobody registered yet!")

        else:
            embed, channel = await scrim.create_slotlist()
            embed.color = ctx.bot.color

            await ctx.send(embed=embed)
            prompt = await ctx.prompt("This is how the slotlist looks. Should I send it?")
            if prompt:
                if channel != None and channel.permissions_for(ctx.me).send_messages:
                    await channel.send(embed=embed)
                    await ctx.success(f"Slotlist sent successfully!")
                else:
                    await ctx.error(f"I can't send messages in {channel}")

            else:
                await ctx.success(f"Ok!")

    @s_slotlist.command(name="edit")
    @checks.can_use_sm()
    async def s_slotlist_edit(self, ctx, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")
        menu = SlotEditor(scrim=scrim)
        await menu.start(ctx)

    @s_slotlist.command(name="image")
    @checks.can_use_sm()
    async def s_slotlist_image(self, ctx, scrim_id: int):
        pass

    # ************************************************************************************************
    @smanager.command(name="delete")
    @checks.can_use_sm()
    async def s_delete(self, ctx, scrim_id: int):
        scrim = await Scrim.get_or_none(pk=scrim_id, guild_id=ctx.guild.id)
        if scrim is None:
            raise ScrimError(f"This is not a valid Scrim ID.\n\nGet a valid ID with `{ctx.prefix}smanager config`")

        prompt = await ctx.prompt(
            f"Are you sure you want to delete scrim `{scrim.id}`?",
        )
        if prompt:
            await scrim.delete()
            await ctx.success(f"Scrim (`{scrim.id}`) deleted successfully.")
        else:
            await ctx.success(f"Alright! Aborting")

    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************

    @commands.group()
    async def tourney(self, ctx):
        pass

    @tourney.command(name="create")
    async def t_create(self, ctx):
        pass


def setup(bot):
    bot.add_cog(ScrimManager(bot))
    bot.add_cog(SMError(bot))
