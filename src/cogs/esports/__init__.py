from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog, Context
from contextlib import suppress
from .utils import (
    delete_denied_message,
    scrim_work_role,
    toggle_channel,
    scrim_end_process,
    tourney_work_role,
)

from utils import inputs, checks, FutureTime, human_timedelta, get_chunks, QuoRole, QuoTextChannel, PastDate

from .converters import PointsConverter, ScrimConverter, TourneyConverter
from constants import EsportsType, IST
from discord.ext.commands.cooldowns import BucketType
from models import *
from datetime import datetime, timedelta
from discord.ext import commands

from .events import ScrimEvents
from .errors import ScrimError, SMError, TourneyError, PointsError
from prettytable import PrettyTable
from .image import ptable_files

import discord
import config
from .menus import *


class ScrimManager(Cog, name="Esports"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, (ScrimError, TourneyError, PointsError)):
            return await ctx.error(error)

    @property
    def reminders(self):
        return self.bot.get_cog("Reminders")

    # ************************************************************************************************

    # ************************************************************************************************

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if message.channel.id in self.bot.scrim_channels:
            scrim = await Scrim.get_or_none(registration_channel_id=message.channel.id)
            if not scrim or not scrim.opened_at:  # either scrim doesn't exist or it is closed.
                return

            if not message.id in (record.message_id for record in await scrim.assigned_slots.all()):
                return

            slot = [
                slot
                for slot in await scrim.assigned_slots.all()
                if slot.user_id == message.author.id and slot.message_id == message.id
            ]
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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
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
            open_role = scrim_work_role(scrim, constants.EsportsRole.open)
            ping_role = scrim_work_role(scrim, constants.EsportsRole.ping)
            mystring = f"> Scrim ID: `{scrim.id}`\n> Name: `{scrim.name}`\n> Registration Channel: {reg_channel}\n> Slotlist Channel: {slot_channel}\n> Role: {role}\n> Mentions: `{scrim.required_mentions}`\n> Total Slots: `{scrim.total_slots}`\n> Open Time: `{open_time}`\n> Toggle: `{scrim.stoggle}`\n> Open Role: {open_role}\n> Ping Role: {ping_role}\n> Slotlist start from: {scrim.start_from}"

            to_paginate.append(f"**`<<<<<<-- {idx:02d}. -->>>>>>`**\n{mystring}\n")

        paginator = Pages(
            ctx, title="Total Scrims: {}".format(len(to_paginate)), entries=to_paginate, per_page=1, show_entry_count=True
        )

        await paginator.paginate()

    # ************************************************************************************************

    @smanager.command(name="toggle")
    @checks.can_use_sm()
    @checks.has_done_setup()
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

    @s_slotlist.command(name="show")
    async def s_slotlist_show(self, ctx, scrim: ScrimConverter):
        """
        Show slotlist of a scrim.
        """
        if not await scrim.teams_registered.count():
            return await ctx.error("Nobody registered yet!")

        embed, channel = await scrim.create_slotlist()
        await ctx.send(embed=embed, embed_perms=True)

    @s_slotlist.command(name="send")
    @checks.can_use_sm()
    @checks.has_done_setup()
    async def s_slotlist_send(self, ctx, scrim: ScrimConverter, channel: QuoTextChannel = None):
        """
        Send slotlist of a scrim.
        """

        if not await scrim.teams_registered.count():
            return await ctx.error("Nobody registered yet!")

        else:
            embed, schannel = await scrim.create_slotlist()
            channel = channel or schannel

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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
    @commands.cooldown(5, 1, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_slotlist_format(self, ctx, scrim: ScrimConverter):
        """Set a default format for scrim slotlist."""
        menu = SlotlistFormatMenu(scrim=scrim)
        await menu.start(ctx)

    @s_slotlist.command(name="image")
    @checks.can_use_sm()
    @checks.has_done_setup()
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
    @checks.has_done_setup()
    async def s_delete(self, ctx, scrim: ScrimConverter):
        """
        Completely delete a scrim.
        """
        prompt = await ctx.prompt(
            f"Are you sure you want to delete scrim `{scrim.id}`?",
        )
        if prompt:
            self.bot.scrim_channels.discard(scrim.registration_channel_id)
            await scrim.delete()
            await ctx.success(f"Scrim (`{scrim.id}`) deleted successfully.")
        else:
            await ctx.success(f"Alright! Aborting")

    @smanager.command(name="ban")
    @checks.can_use_sm()
    @checks.has_done_setup()
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
    @checks.has_done_setup()
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
    @checks.can_use_sm()
    @checks.has_done_setup()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_reserve(self, ctx, scrim: ScrimConverter):
        """
        Add / Remove a team from the reserved list
        """
        menu = ReserveEditorMenu(scrim=scrim)
        await menu.start(ctx)

    @s_reserve.command(name="list", aliases=("all",))
    @checks.can_use_sm()
    @checks.has_done_setup()
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

    @smanager.command(name="autoclean")
    @checks.can_use_sm()
    @checks.has_done_setup()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_autoclean(self, ctx, scrim: ScrimConverter):
        """Commands related to quotient's autoclean"""
        await AutocleanMenu(scrim=scrim).start(ctx)

    @smanager.command(name="info")
    async def s_info(self, ctx: Context, scrim: ScrimConverter):
        """Get information about a scrim."""
        text = (
            f"> Name: `{scrim.name}`\n> Registration Channel: {getattr(scrim.registration_channel,'mention','`Channel Not Found`')}\n"
            f"> Slotlist Channel: {getattr(scrim.slotlist_channel,'mention','`Channel Not Found`')}\n"
            f"> Total Slots: `{scrim.total_slots}`\n\nRegistration status?"
        )
        if scrim.opened_at:
            text += f"\n> `Open!` ({strtime(scrim.opened_at)})\n> Slots Left: {len(scrim.available_slots)}"

        elif scrim.closed_at:
            text += f"\n> `Closed!` ({strtime(scrim.closed_at)})"

        else:
            text += "\n> Will be available after next registrations!"

        banned = [x.user_id for x in await scrim.banned_teams]
        text += f"\n\n> Reserved Slots: `{sum(1 for i in (x.user_id for x in await scrim.reserved_slots))}`"
        text += f"\n> Banned Users: `{len(banned)}` "
        if len(banned):
            text += ", ".join((getattr(x, "mention", "Not Found!") for x in map(self.bot.get_user, banned)))

        embed = self.bot.embed(ctx, title="Scrims Info: ({0})".format(scrim.id))
        embed.description = text
        await ctx.send(embed=embed, embed_perms=True)

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
                tourney_mod = await ctx.guild.create_role(name="tourney-mod", color=0x00FFB3, reason=reason)

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
    @checks.has_done_setup()
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
            open_role = tourney_work_role(tourney)
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
    @checks.has_done_setup()
    async def tourney_delete(self, ctx, tourney_id: TourneyConverter):
        """Delete a tournament"""
        tourney = tourney_id
        prompt = await ctx.prompt(
            f"Are you sure you want to delete tournament `{tourney.id}`?",
        )
        if prompt:
            self.bot.tourney_channels.discard(tourney.registration_channel_id)
            await tourney.delete()
            await ctx.success(f"Tourney (`{tourney.id}`) deleted successfully.")
        else:
            await ctx.success(f"Alright! Aborting")

    @tourney.command(name="groups")
    @checks.can_use_tm()
    @checks.has_done_setup()
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def tourney_group(self, ctx, tourney: TourneyConverter, group_size: int = 20):
        """Get groups of the tournament."""
        records = await tourney.assigned_slots.all().order_by("id")
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
    @checks.has_done_setup()
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    async def tourney_data(self, ctx, tourney: TourneyConverter):
        """Get all the data that Quotient collected for a tourney."""
        records = await tourney.assigned_slots.all().order_by("id")
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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def tourney_edit(self, ctx, tourney: TourneyConverter):
        """Edit a tournament's config."""

        menu = TourneyEditor(tourney=tourney)
        await menu.start(ctx)

    @tourney.command(name="start")
    @checks.can_use_tm()
    @checks.has_done_setup()
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
            self.bot.tourney_channels.add(channel.id)
            await Tourney.filter(pk=tourney.id).update(started_at=datetime.now(tz=IST), closed_at=None)
            await channel.send("**Registration is now Open!**")
            await ctx.message.add_reaction(emote.check)
        else:
            await ctx.success("OK!")

    @tourney.command(name="stop", aliases=("pause",))
    @checks.can_use_tm()
    @checks.has_done_setup()
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
    @checks.has_done_setup()
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
    @checks.has_done_setup()
    async def tourney_unban(self, ctx, tourney: TourneyConverter, user: discord.User):
        """Unban a banned user from tournament."""
        if user.id not in tourney.banned_users:
            return await ctx.send(
                f"**{str(user)}** is not banned the tourney.\n\nUse `{ctx.prefix}tourney ban {tourney.id} {user}` to ban them."
            )

        await Tourney.filter(pk=tourney.id).update(banned_users=ArrayRemove("banned_users", user.id))
        await ctx.success(f"**{str(user)}** has been successfully unbanned from Tourney (`{tourney.id}`)")

    @tourney.command(name="info")
    async def tourney_info(self, ctx: Context, tourney: TourneyConverter):
        """Get all the necessary info about a tourney."""
        text = (
            f"> Name: `{tourney.name}`\n"
            f"> Registration Channel: {getattr(tourney.registration_channel,'mention','`Channel Not Found`')}\n"
            f"> Confirmation Channel: {getattr(tourney.confirm_channel,'mention','`Channel Not Found`')}\n"
            f"> Total Slots: `{tourney.total_slots}`\n\nRegistraton Status?"
        )
        left = tourney.total_slots - len(await tourney.assigned_slots.all())

        if tourney.started_at:
            text += f"\n> `Open!` ({strtime(tourney.started_at)})\n> Slots Left: {left}"

        else:
            text += f"\n> `Closed!` ({strtime(tourney.closed_at)})"

        embed = self.bot.embed(ctx, title="Tourney Config: ({0})".format(tourney.id))
        embed.description = text
        await ctx.send(embed=embed, embed_perms=True)

    @commands.command()
    async def format(self, ctx, *, registration_form):
        """Get your reg-format in a reusable form."""
        await ctx.send(f"```{registration_form}```")

    @commands.command()
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    @checks.can_use_sm()
    async def quickidp(self, ctx, room_id, password, map, role_to_ping: QuoRole = None):
        """
        Share Id/pass with embed quickly.
        Message is automatically deleted after 30 minutes.
        """
        await ctx.message.delete()
        embed = self.bot.embed(ctx, title="New Custom Room. JOIN NOW!")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Room ID", value=room_id)
        embed.add_field(name="Password", value=password)
        embed.add_field(name="Map", value=map)
        embed.set_footer(text=f"Shared by: {ctx.author} • Auto delete in 30 minutes.", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(
            content=role_to_ping.mention if role_to_ping else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        self.bot.loop.create_task(delete_denied_message(msg, 30 * 60))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(7, 1, type=commands.BucketType.guild)
    async def customidp(self, ctx, channel: QuoTextChannel, role_to_ping: QuoRole = None):
        """Share customized Id/pass message."""
        if not (
            channel.permissions_for(ctx.me).send_messages
            or channel.permissions_for(ctx.me).embed_links
            or channel.permissions_for(ctx.me).manage_messages
        ):
            return await ctx.error(
                f"I need `send_messages` , `embed_links` and `manage_messages` permission in {channel.mention}"
            )

        await IDPMenu(send_channel=channel, role=role_to_ping).start(ctx)

    @commands.group(aliases=("eztag",), invoke_without_command=True)
    async def easytag(self, ctx: Context):
        """Commands related to quotient's eztag"""
        await ctx.send_help(ctx.command)

    @easytag.command(name="set")
    @checks.has_done_setup()
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_permissions(manage_guild=True)
    async def set_eztag(self, ctx: Context, *, channel: QuoTextChannel):
        """Set a channel as eztag channel."""
        count = await EasyTag.filter(guild_id=ctx.guild.id).count()
        guild = await Guild.get(guild_id=ctx.guild.id)

        if count == 1 and not guild.is_premium:
            return await ctx.error(
                f"Upgrade your server to Quotient Premium to setup more than 1 EasyTag channel.\n{self.bot.config.WEBSITE}/premium"
            )

        if channel.id in self.bot.eztagchannels:
            return await ctx.error(f"This channel is already a easy tag channel.")

        if (
            not channel.permissions_for(ctx.me).send_messages
            or not channel.permissions_for(ctx.me).embed_links
            or not channel.permissions_for(ctx.me).manage_messages
        ):
            return await ctx.error(
                f"I need `send_messages`, `embed_links` and `manage_messages` permission in {channel.mention}"
            )

        role = discord.utils.get(ctx.guild.roles, name="quotient-tag-ignore")
        if not role:
            role = await ctx.guild.create_role(
                name="quotient-tag-ignore", color=0x00FFB3, reason=f"Created by {ctx.author}"
            )

        await EasyTag.create(guild_id=ctx.guild.id, channel_id=channel.id)
        self.bot.eztagchannels.add(channel.id)

        embed = self.bot.embed(ctx, title="Easy Tagging")
        embed.description = """
        Unable to mention teammates while registering for scrims or tournaments? Quotient is here for the rescue.

        Use `teammate's ID`, `@teammate_name` or `@teammate's_discord_tag` in your registration format. Quotient will convert that into an actual discord tag.        
        """
        embed.set_image(url="https://media.discordapp.net/attachments/775707108192157706/850788091236450344/eztags.gif")
        msg = await channel.send(embed=embed)
        await msg.pin()

        await ctx.success(
            f"Successfully added **{channel}** to easy tag channels.\n\nAdd {role.mention} to your roles to ignore your messages in **{channel}**"
        )

    @easytag.command(name="remove")
    @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    async def remove_eztag(self, ctx: Context, *, channel: QuoTextChannel):
        """Remove a eztag channel"""
        if not channel.id in self.bot.eztagchannels:
            return await ctx.error(f"This is not a EasyTag channel.")

        await EasyTag.filter(channel_id=channel.id).delete()
        self.bot.eztagchannels.discard(channel.id)
        await ctx.success(f"Removed {channel} from EasyTag channels.")

    @easytag.command(name="config")
    @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    async def config_eztag(self, ctx: Context):
        """Get a list of all your easytag channels."""
        records = await EasyTag.filter(guild_id=ctx.guild.id)
        if not len(records):
            return await ctx.error(
                f"You haven't set any easytag channel yet.\n\nUse `{ctx.prefix}eztag set #{ctx.channel}`"
            )

        eztags = []
        for idx, record in enumerate(records, start=1):
            channel = getattr(record.channel, "mention", record.channel_id)
            eztags.append(
                f"`{idx:02}.` {channel} (Delete After: {record.delete_after if record.delete_after else 'Not Set'})"
            )

        embed = self.bot.embed(ctx, title="EasyTag config", description="\n".join(eztags))
        await ctx.send(embed=embed)

    @easytag.command(name="autodelete")
    @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    async def delete_eztag(self, ctx: Context, channel: QuoTextChannel):
        """Enable/Disable autodelete for eztag."""
        record = await EasyTag.get_or_none(channel_id=channel.id)
        if not record:
            return await ctx.error(f"This is not a EasyTag Channel.")

        await EasyTag.filter(channel_id=channel.id).update(delete_after=not record.delete_after)
        await ctx.success(
            f"Delete After for **{channel}** turned {'ON' if not record.delete_after else 'OFF'}!\n\nDelete After automatically deletes the format message after some time."
        )

    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************

    @commands.group(invoke_without_command=True, aliases=("tc",))
    async def tagcheck(self, ctx: Context):
        """
        Setup tagcheck channels for scrims/tournaments.
        """
        await ctx.send_help(ctx.command)

    @tagcheck.command(name="set")
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_set(self, ctx: Context, channel: discord.TextChannel, mentions=0):
        """
        Set a channel for tagcheck.
        mentions means required mentions, It's zero by default.
        """
        count = await TagCheck.filter(guild_id=ctx.guild.id).count()
        guild = await Guild.get(guild_id=ctx.guild.id)

        if count == 1 and not guild.is_premium:
            return await ctx.error(
                f"Upgrade your server to Quotient Premium to setup more than 1 Tagcheck channel.\n{self.bot.config.WEBSITE}/premium"
            )

        if channel.id in self.bot.tagcheck:
            return await ctx.error(f"This channel is already a tagcheck channel.")

        if (
            not channel.permissions_for(ctx.me).send_messages
            or not channel.permissions_for(ctx.me).embed_links
            or not channel.permissions_for(ctx.me).manage_messages
        ):
            return await ctx.error(
                f"I need `send_messages`, `embed_links` and `manage_messages` permission in {channel.mention}"
            )

        role = discord.utils.get(ctx.guild.roles, name="quotient-tag-ignore")
        if not role:
            role = await ctx.guild.create_role(
                name="quotient-tag-ignore", color=0x00FFB3, reason=f"Created by {ctx.author}"
            )

        await TagCheck.create(guild_id=ctx.guild.id, channel_id=channel.id, required_mentions=mentions)
        self.bot.tagcheck.add(channel.id)

        await ctx.success(
            f"Successfully added **{channel}** to tagcheck channels.\n\nAdd {role.mention} to your roles to ignore your messages in **{channel}**"
        )

    @tagcheck.command(name="config")
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_config(self, ctx: Context):
        """
        Get tagcheck config.
        """
        records = await TagCheck.filter(guild_id=ctx.guild.id)
        if not len(records):
            return await ctx.error(
                f"You haven't set any tagcheck channel yet.\n\nUse `{ctx.prefix}tagcheck set #{ctx.channel}`"
            )

        tags = []
        for idx, record in enumerate(records, start=1):
            channel = getattr(record.channel, "mention", record.channel_id)
            tags.append(
                f"`{idx:02}.` {channel} (Mentions: {record.required_mentions},Auto-delete: {record.delete_after if record.delete_after else 'Not Set'})"
            )

        embed = self.bot.embed(ctx, title="TagCheck config", description="\n".join(tags))
        await ctx.send(embed=embed)

    @tagcheck.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_remove(self, ctx: Context, *, channel: QuoTextChannel):
        """Remove a channel from tagcheck"""
        if not channel.id in self.bot.tagcheck:
            return await ctx.error(f"This is not a TagCheck channel.")

        await TagCheck.filter(channel_id=channel.id).delete()
        self.bot.tagcheck.discard(channel.id)
        await ctx.success(f"Removed {channel} from TagCheck channels.")

    @tagcheck.command(name="autodelete")
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_autodelete(self, ctx: Context, *, channel: QuoTextChannel):
        """Enable/Disable autodelete wrong tagchecks."""
        record = await TagCheck.get_or_none(channel_id=channel.id)
        if not record:
            return await ctx.error(f"This is not a TagCheck Channel.")

        await TagCheck.filter(channel_id=channel.id).update(delete_after=not record.delete_after)
        await ctx.success(
            f"Autodelete for **{channel}** turned {'ON' if not record.delete_after else 'OFF'}!\nThis automatically deletes the wrong format message after some time."
        )

    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************

    async def pointsembed(self, ctx: Context, value: int, description: str):
        embed = discord.Embed(color=ctx.bot.color, title=f"📊 Points Table Setup • ({value}/4)")
        embed.description = description
        embed.set_footer(text=f'Reply with "cancel" to stop the process.', icon_url=ctx.bot.user.avatar_url)
        return await ctx.send(embed=embed, embed_perms=True)

    @commands.group(aliases=("pt",), invoke_without_command=True)
    async def ptable(self, ctx):
        await ctx.send_help(ctx.command)

    @ptable.command(name="setup")
    async def ptable_setup(self, ctx: Context):
        count = await PointsInfo.filter(guild_id=ctx.guild.id).count()

        if count >= 2 and not await ctx.is_premium_guild():
            raise PointsError(
                f"You cannot create more than 2 point table setup in free tier.\nKindly checkout [Quotient Premium]({config.WEBSITE}/premium) to enjoy unlimited point table setup."
            )

        def check(message: discord.Message):
            if message.content.strip().lower() == "cancel":
                raise PointsError("Alright, reverting all process.")

            return message.author == ctx.author and ctx.channel == message.channel

        ptinfo = PointsInfo(guild_id=ctx.guild.id)

        await self.pointsembed(
            ctx, 1, "How many points due you want to give per kill?\n\n`Please enter a number between 0 and 10`"
        )
        kill_point = await inputs.integer_input(ctx, check, limits=(0, 10))
        ptinfo.kill_points = kill_point

        await self.pointsembed(
            ctx, 2, "What should be the title of every points table?\n\n`Please keep the character length under 150`"
        )
        title = await inputs.string_input(ctx, check)
        if len(title) > 150:
            raise PointsError("Character length of title cannot exceed 150 characters.")
        ptinfo.title = title

        await self.pointsembed(
            ctx,
            3,
            "In which channel do you want me to send points tables?\n\n`Please mention a channel or write its name`",
        )
        channel = await inputs.channel_input(ctx, check)
        if not channel.permissions_for(ctx.me).embed_links:
            raise PointsError(
                f"Kindly make sure I have `add_reactions`, `send_messages` and `embed_links` permission in {channel.mention}"
            )
        ptinfo.channel_id = channel.id

        await self.pointsembed(
            ctx,
            4,
            "What should be default position points format?\n"
            "Format:\n`<Rank> = <Place Point>`\nRank can be a single number or a range\n"
            "Separate them with comma (`,`)\n"
            "Example:\n"
            "```1 = 20,\n"
            "2 = 14,\n"
            "3-5 = 10```\n"
            "Here, from 6th, everyone will get `0` posi points.",
        )

        points = await inputs.string_input(ctx, check)

        result = {}
        try:
            for line in points.replace("\n", "").split(","):
                line_values = [value.strip() for value in line.split("=")]
                points = int(line_values[1])
                if points > 99:
                    raise PointsError(f"You cannot give more than 99 points to any rank.")

                if "-" in line_values[0]:
                    range_idx = line_values[0].split("-")
                    num_range = [i for i in range(int(range_idx[0]), int(range_idx[1]) + 1)]
                    for key in num_range:
                        result[key] = points
                else:
                    result[int(line_values[0])] = points

        except (ValueError, IndexError):
            raise PointsError(
                "You didn't provide a valid default points format.\n\nClick me to get an example of valid format."
            )

        if len(result) > 25:
            raise PointsError("You can only set position points till rank 25.")

        result = dict(sorted(result.items()))

        ptinfo.posi_points = result

        await ptinfo.save()
        await ctx.success(
            f"Successfully create Points Setup. \nYour points id is `{ptinfo.id}`.\n\nUse `{ctx.prefix}pt match create {ptinfo.id}` to create a new points table."
        )

    @ptable.command(name="config")
    async def points_config(self, ctx: Context):
        records = await PointsInfo.filter(guild_id=ctx.guild.id).all()
        if not len(records):
            raise PointsError(
                f"You haven't create any points table setup yet.\n\nKindly use `{ctx.prefix}pt setup` to create one."
            )

        to_pagi = []
        for idx, record in enumerate(records, start=1):
            text = f"`{idx:02})` Points ID: `{record.id}` | **{record.title}** | Per Kill: `{record.kill_points}`\n"
            to_pagi.append(text)

        paginator = Pages(
            ctx,
            title="Total Points Setup: {}".format(len(to_pagi)),
            entries=to_pagi,
            per_page=10,
            show_entry_count=True,
        )
        await paginator.paginate()

    @ptable.command(name="edit")
    async def points_edit(self, ctx: Context, points_id: PointsConverter):
        await PointsConfigEditor(points=points_id).start(ctx)

    @ptable.command(name="leaderboard", aliases=("lb",))
    async def points_leaderboard(self, ctx: Context, points_id: PointsConverter, days: typing.Optional[int] = 7):
        date = datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days)
        records = await points_id.data.filter(created_at__gte=date).all()
        if not records:
            raise PointsError(
                f"You haven't created any points table between `{date.strftime('%d-%b-%Y')}` and `{datetime.now().strftime('%d-%b-%Y')}`"
            )

        d1 = literal_eval(records[0].points_table)

        ds = [literal_eval(record.points_table) for record in records]

        d = {}
        for k in d1.keys():
            myiter = tuple(d[k] for d in ds)
            d[k] = tuple(map(sum, zip(*myiter)))

        d.update(dict(sorted(d.items(), reverse=True, key=lambda x: x[1][3])))
        await ctx.send(d)

    @ptable.command(name="delete")
    async def points_delete(self, ctx: Context, points_id: PointsConverter):
        prompt = await ctx.prompt(
            f"Points Table setup ({points_id.id}) will be deleted, along with all its matches.",
            title="Are you sure you want to continue?",
        )
        if not prompt:
            return await ctx.success("ok, Aborting")

        await PointsInfo.filter(id=points_id.id).delete()
        await ctx.send(f"Deleted points setup (`{points_id.id}`)")

    @ptable.group(name="match", invoke_without_command=True)
    async def _ptable(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @_ptable.command(name="create")
    async def _ptable_create(self, ctx: Context, points_id: PointsConverter):
        points = points_id
        record = await points.data.filter(
            created_at__gte=datetime.now(constants.IST).replace(hour=0, minute=0, second=0, microsecond=0)
        ).first()
        if record:
            raise PointsError(
                "You have already created today's points table. If you want to delete it and create a new one,\n"
                f"Kindly use: `{ctx.prefix}pt match delete {points.id}`\n"
                f"If you want to see, what is looks like, use: `{ctx.prefix}pt match show {record.id}`"
            )

        msg = await ctx.simple(
            "Starting the Points Table Creator...\n\n`Tip:` It is recommended to use this command on a computer."
        )
        await asyncio.sleep(2)
        await PointsMenu(points=points_id, msg=msg).start(ctx)

    @_ptable.command(name="all")
    async def _ptable_all(self, ctx: Context, points_id: PointsConverter):
        records = await points_id.data.all()
        if not records:
            raise PointsError(
                f"You haven't created any match yet.\n\nKindly use `{ctx.prefix}pt match create {points_id.id}`"
            )

        matches = []
        for idx, record in enumerate(records, start=1):
            matches.append(f"`{idx:02}` **{record.created_at.strftime('%d-%m-%Y')}** (<@{record.created_by}>)")

        paginator = Pages(
            ctx,
            title="Total Points Tables: {}".format(len(matches)),
            entries=matches,
            per_page=12,
            show_entry_count=True,
            footertext=f'Use "{ctx.prefix}pt match show {points_id.id} <date>" to get image version',
        )
        await paginator.paginate()

    @_ptable.command(name="show")
    async def _ptable_show(self, ctx: Context, points_id: PointsConverter, *, date: typing.Optional[PastDate]):
        date = date or datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)

        data = await points_id.data.filter(created_at=date).first()

        if not data:
            raise PointsError(f"I couldn't find any points table created on **{date.strftime('%d/%b/%Y')}**")

        files = await ptable_files(points_id, data)
        if len(files):
            for file in files:
                embed = self.bot.embed(ctx)
                embed.set_image(url="attachment://points_table.png")
                embed.set_footer(text=f"Date: {data.created_at.strftime('%d/%b/%Y')}")
                await ctx.send(file=file, embed=embed)

        else:
            raise PointsError(
                f"You haven't saved any points in the points table.\n\nKindly delete it with `{ctx.prefix}pt match delete {points_id.id}`\nand create a new one again."
            )

    @_ptable.command(name="send")
    async def _ptable_send(self, ctx: Context, points_id: PointsConverter, *, date: typing.Optional[PastDate]):
        date = date or datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)

        data = await points_id.data.filter(created_at=date).first()

        if not data:
            raise PointsError(f"I couldn't find any points table created on **{date.strftime('%d/%b/%Y')}**")

        channel = points_id.channel

        if not channel:
            raise PointsError(f"I couldn't find default points table send channel for `{points_id.id}`")

        perms = channel.permissions_for(ctx.me)

        if not all((perms.send_messages, perms.embed_links)):
            raise PointsError(
                f"Kindly make sure I have following permissions in {channel.mention}:\n\n- `send messages`\n- `embed links`"
            )

        files = await ptable_files(points_id, data)
        if not len(files):
            raise PointsError(
                f"You haven't saved any points in the points table.\n\nKindly delete it with `{ctx.prefix}pt match delete {points_id.id}`\nand create a new one again."
            )

        for file in files:
            embed = self.bot.embed(ctx)
            embed.set_image(url="attachment://points_table.png")
            embed.set_footer(text=f"Date: {data.created_at.strftime('%d/%b/%Y')}")
            await channel.send(file=file, embed=embed)

        await ctx.success(f"Sent points table successfully.")

    @_ptable_show.before_invoke
    @_ptable_send.before_invoke
    async def before_points_invoke(self, ctx):
        await ctx.trigger_typing()

    @_ptable.command(name="delete")
    async def _ptable_delete(self, ctx: Context, points_id: PointsConverter, *, date: typing.Optional[PastDate]):
        date = date or datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)
        points = points_id
        record = await points.data.filter(created_at=date).first()
        if not record:
            raise PointsError(f"No points table found for date: `{date.strftime('%d-%b-%Y')}`")

        prompt = await ctx.prompt(
            "Are you sure you want to delete the points table created on `{0}`".format(date.strftime("%d-%b-%Y"))
        )
        if not prompt:
            return await ctx.success("ok Aborting")

        await PointsTable.filter(id=record.id).delete()
        return await ctx.success("Successfully deleted points table.")


def setup(bot):
    bot.add_cog(ScrimManager(bot))
    bot.add_cog(SMError(bot))
    bot.add_cog(ScrimEvents(bot))
