from __future__ import annotations

import typing

from cogs.esports.events.slots import SlotManagerEvents
from cogs.esports.views.scrims.main import ScrimsMain
from cogs.esports.views.tourney.main import TourneyManager

if typing.TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from datetime import datetime

import discord
from discord.ext import commands

from constants import IST
from core import Cog, Context, QuotientView
from models import *
from utils import QuoRole, QuoTextChannel, QuoUser, checks

from .errors import PointsError, ScrimError, SMError, TourneyError
from .events import ScrimEvents, Ssverification, TagEvents, TourneyEvents
from .helpers import MultiScrimConverter, delete_denied_message
from .menus import *
from .views import *


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

        if message.channel.id in self.bot.cache.scrim_channels:
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
            if not slot:  # means their registration was denied
                return
            slot = slot[0]

            self.bot.dispatch("scrim_registration_delete", scrim, message, slot)

    # ************************************************************************************************

    @commands.group(aliases=("s", "sm"), invoke_without_command=True)
    async def smanager(self, ctx: Context):
        """
        Contains commands related to Quotient's powerful scrims manager.
        """
        v = ScrimsMain(ctx)
        v.message = await ctx.send(embed=await v.initial_embed(), view=v)

    # ************************************************************************************************
    # *************************************************************
    @smanager.group(name="slotlist", invoke_without_command=True)
    async def s_slotlist(self, ctx):
        """
        Create/ Edit or Send a scrim slotlist.
        """
        await ctx.send_help(ctx.command)

    @s_slotlist.command(name="show")
    async def s_slotlist_show(self, ctx, scrim: Scrim):
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
    async def s_slotlist_send(self, ctx: Context, scrim: Scrim, channel: discord.TextChannel = None):
        """
        Send slotlist of a scrim.
        """
        if not await scrim.teams_registered.count():
            return await ctx.error("Nobody registered yet!")

        embed, schannel = await scrim.create_slotlist()
        channel = channel or schannel

        await ctx.send(embed=embed)
        prompt = await ctx.prompt("This is how the slotlist looks. Should I send it?")
        if not prompt:
            return await ctx.error("Ok, Aborting.")

        if channel is not None and channel.permissions_for(ctx.me).embed_links:
            _v = SlotlistEditButton(ctx.bot, scrim)

            _v.message = await channel.send(embed=embed, view=_v)
            await ctx.success("Slotlist sent successfully!")

            if channel == schannel:
                await Scrim.filter(pk=scrim.id).update(slotlist_message_id=_v.message.id)

        else:
            await ctx.error(f"I can't send messages in {channel}")

    @s_slotlist.command(name="format")
    @checks.can_use_sm()
    @commands.cooldown(5, 1, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    async def s_slotlist_format(self, ctx, scrim: Scrim):
        """Set a default format for scrim slotlist."""
        view = SlotlistFormatter(ctx, scrim=scrim)
        view.message = await ctx.send(embed=SlotlistFormatter.updated_embed(scrim), view=view)

    @smanager.command(name="start")
    @checks.can_use_sm()
    @checks.has_done_setup()
    @commands.cooldown(10, 1, type=commands.BucketType.user)
    async def s_start(self, ctx: Context, scrim: Scrim):
        """
        Start a registration instantly.
        """
        ...
        prompt = await ctx.prompt(
            f"This will start the registrations for {str(scrim)} will start immediately."
            "\nAlso the registraton open time will change to current time, \n\n"
            "Are you sure you want to continue?"
        )

        if not prompt:
            return await ctx.simple("Alright, Aborting")

        _t = datetime.now(tz=IST)
        await Scrim.filter(pk=scrim.id).update(open_time=_t)
        await self.reminders.create_timer(_t, "scrim_open", scrim_id=scrim.id)
        await ctx.success(
            f"Registration opened!\n\nRegistration open time has been changed to `{_t.strftime('%I:%M %p')}`"
            f"\nYou can change open time again with `{ctx.prefix}s edit {scrim.id}`"
        )

    # ************************************************************************************************

    @smanager.command(name="ban")
    @checks.can_use_sm()
    @checks.has_done_setup()
    async def s_ban(self, ctx: Context):
        """
        Ban someone from the scrims temporarily or permanently.
        """
        await ctx.simple("Use 'Punish' button from the slotlist message. ")

    @smanager.command(name="unban")
    @checks.can_use_sm()
    @checks.has_done_setup()
    async def s_unban(self, ctx: Context, scrim: MultiScrimConverter, user: QuoUser, *, reason: str = None):
        """
        Unban a banned team from a scrim.
        Use `all` to unban from all scrims.
        """
        if len(scrim) == 1 and not user.id in await scrim[0].banned_user_ids():
            return await ctx.send(f"**{str(user)}** is not banned.")

        scrims = []
        for s in scrim:
            bans = await s.banned_teams.filter(user_id=user.id)
            if bans:
                await BannedTeam.filter(id__in=[_.pk for _ in bans]).delete()
                scrims.append(s)

        if not scrims:
            return await ctx.send(f"**{str(user)}** is not banned from scrims.")

        format = "\n".join(
            (
                f"{emote.check} Scrim {scrim.id}: {getattr(scrim.registration_channel, 'mention','deleted-channel')}"
                for scrim in scrims
            )
        )

        await ctx.simple(f"Successfully unbanned {str(user)} from \n" f"{format}")

        if banlog := await BanLog.get_or_none(guild_id=ctx.guild.id):
            await banlog.log_unban(user.id, ctx.author, scrims, reason or "```No reason given```")

    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************
    # ************************************************************************************************

    @commands.command(aliases=("tm", "t"))
    @commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
    @commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def tourney(self, ctx: Context):
        """Create & Manage tournaments with Quotient"""
        if not Tourney.is_ignorable(ctx.author) and not ctx.author.guild_permissions.manage_guild:
            return await ctx.error(
                "You need either `manage-server` permissions or `@tourney-mod` role to manage tournaments."
            )

        view = TourneyManager(ctx)
        view.add_item(QuotientView.tricky_invite_button())
        view.message = await ctx.send(embed=await view.initial_embed(), view=view)

    @commands.command(extras={"examples": ["quickidp 1234 pass Miramar", "quickidp 1234 pass Sanhok @role"]})
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    @checks.can_use_sm()
    @commands.cooldown(7, 1, type=commands.BucketType.guild)
    async def quickidp(self, ctx: Context, room_id, password, map, role_to_ping: QuoRole = None):
        """
        Share Id/pass with embed quickly.
        Message is automatically deleted after 30 minutes.
        """
        await ctx.message.delete()
        embed = self.bot.embed(ctx, title="New Custom Room. JOIN NOW!")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.add_field(name="Room ID", value=room_id)
        embed.add_field(name="Password", value=password)
        embed.add_field(name="Map", value=map)
        embed.set_footer(
            text=f"Shared by: {ctx.author} • Auto delete in 30 minutes.", icon_url=ctx.author.display_avatar.url
        )
        msg = await ctx.send(
            content=role_to_ping.mention if role_to_ping else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )

        self.bot.loop.create_task(delete_denied_message(msg, 30 * 60))

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(7, 1, type=commands.BucketType.guild)
    async def customidp(self, ctx: Context, channel: QuoTextChannel, role_to_ping: QuoRole = None):
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
                f"Upgrade your server to Quotient Premium to setup more than 1 EasyTag channel.\n[Click Me to Purchase]({self.bot.prime_link})"
            )

        if channel.id in self.bot.cache.eztagchannels:
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
                name="quotient-tag-ignore", color=self.bot.color, reason=f"Created by {ctx.author}"
            )

        await EasyTag.create(guild_id=ctx.guild.id, channel_id=channel.id)
        self.bot.cache.eztagchannels.add(channel.id)

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
        if not channel.id in self.bot.cache.eztagchannels:
            return await ctx.error(f"This is not a EasyTag channel.")

        await EasyTag.filter(channel_id=channel.id).delete()
        self.bot.cache.eztagchannels.discard(channel.id)
        await ctx.success(f"Removed {channel} from EasyTag channels.")

    @easytag.command(name="config")
    @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    async def config_eztag(self, ctx: Context):
        """Get a list of all your easytag channels."""
        records = await EasyTag.filter(guild_id=ctx.guild.id)
        if not records:
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

    @tagcheck.command(name="set", extras={"examples": ["tc set #channel 4", "tagcheck set #channel 2"]})
    @commands.has_permissions(manage_guild=True)
    @checks.has_done_setup()
    async def tagcheck_set(self, ctx: Context, channel: discord.TextChannel, mentions: int):
        """
        Set a channel for tagcheck.
        mentions means required mentions, It's zero by default.
        """
        count = await TagCheck.filter(guild_id=ctx.guild.id).count()
        guild = await Guild.get(guild_id=ctx.guild.id)

        if count == 1 and not guild.is_premium:
            return await ctx.error(
                f"Upgrade your server to Quotient Premium to setup more than 1 Tagcheck channel.\n[Click Me to Purchase]({self.bot.prime_link})"
            )

        if channel.id in self.bot.cache.tagcheck:
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
                name="quotient-tag-ignore", color=self.bot.color, reason=f"Created by {ctx.author}"
            )

        await TagCheck.create(guild_id=ctx.guild.id, channel_id=channel.id, required_mentions=mentions)
        self.bot.cache.tagcheck.add(channel.id)

        await ctx.success(
            f"Successfully added **{channel}** to tagcheck channels.\n\nAdd {role.mention} to your roles to ignore your messages in **{channel}**"
        )

    @tagcheck.command(name="config")
    @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    async def tagcheck_config(self, ctx: Context):
        """
        Get tagcheck config.
        """
        records = await TagCheck.filter(guild_id=ctx.guild.id)
        if not records:
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
        if not channel.id in self.bot.cache.tagcheck:
            return await ctx.error(f"This is not a TagCheck channel.")

        await TagCheck.filter(channel_id=channel.id).delete()
        self.bot.cache.tagcheck.discard(channel.id)
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

    # @commands.group(aliases=("pt",), invoke_without_command=True)
    # async def ptable(self, ctx):
    #     """Points tables commands"""
    #     embed = discord.Embed(color=self.bot.color, title="Shifted to Dashboard", url=self.bot.config.WEBSITE)
    #     embed.description = (
    #         f"Points table command has been moved to the dashboard [here]({self.bot.config.WEBSITE}/dashboard) for ease of use."
    #         f"\n\nTo create beautiful points tables, use the link above or use `{ctx.prefix}dashboard` command to get a direct link"
    #         "to the dashboard"
    #     )
    #     embed.set_image(url="https://media.discordapp.net/attachments/779229002626760716/873236858333720616/ptable.png")
    #     await ctx.send(embed=embed, embed_perms=True)

    @commands.command(aliases=("slotm",))
    @commands.bot_has_guild_permissions(embed_links=True, manage_messages=True, manage_channels=True)
    @checks.has_done_setup()
    async def slotmanager(self, ctx: Context):
        """
        SlotManager helps people to setup scrims-slots cancel and claim manager.
        Users can easily claim and cancel their slots anytime without bothering mods.
        """
        _view = ScrimsSlotManagerSetup(ctx)
        _e = await _view.initial_message(ctx.guild)
        _view.add_item(QuotientView.tricky_invite_button())
        _view.message = await ctx.send(embed=_e, view=_view, embed_perms=True)

    @commands.command(name="banlog")
    @checks.can_use_sm()
    async def _banlog(self, ctx: Context, *, channel: discord.TextChannel = None):
        """
        Set a channel for all scrims ban/unban logs
        """
        if not channel:
            record = await BanLog.get_or_none(guild_id=ctx.guild.id)
            if not record:
                return await ctx.simple(
                    f"You haven't setup any esports ban log channel yet.\n"
                    f"Use `{ctx.prefix}banlog #{ctx.channel}` to do it."
                )
            return await ctx.simple(
                f"Currently {getattr(record.channel, 'mention', 'deleted-channel')} is serving as ban/unban log channel."
            )
        if not channel.permissions_for(ctx.me).embed_links:
            return await ctx.error(f"I need `embed_links` permission in {channel.mention} to send logs.")

        await BanLog.update_or_create(guild_id=ctx.guild.id, defaults={"channel_id": channel.id})
        await ctx.success(f"Successfully set {channel.mention} as esports ban/unban log channel.")

    @commands.group(invoke_without_command=True, aliases=("ss",))
    @checks.can_use_tm()
    @commands.bot_has_permissions(manage_channels=True, add_reactions=True, embed_links=True, manage_roles=True)
    async def ssverify(self, ctx: Context):
        """
        Setup/Edit ssverification in your server
        """
        if not await ctx.is_premium_guild():
            if not ctx.guild.member_count > 100 and not ctx.guild.id == 779229001986080779:
                return await ctx.error("Your server must have atleast 100 members to setup ssverification.")

        _view = SsmodMainView(ctx)
        _view.message = await ctx.send(embed=await _view.initial_message(), view=_view, embed_perms=True)


def setup(bot):
    bot.add_cog(ScrimManager(bot))
    bot.add_cog(SMError(bot))
    bot.add_cog(ScrimEvents(bot))
    bot.add_cog(TourneyEvents(bot))
    bot.add_cog(TagEvents(bot))
    bot.add_cog(Ssverification(bot))
    bot.add_cog(SlotManagerEvents(bot))
