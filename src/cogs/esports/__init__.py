from __future__ import annotations

import typing

from cogs.esports.events.slots import SlotManagerEvents
from cogs.esports.views.scrims.main import ScrimsMain
from cogs.esports.views.tourney.main import TourneyManager

if typing.TYPE_CHECKING:
    from core import Quotient

import discord
from discord.ext import commands

from core import Cog, Context, QuotientView
from models import *
from utils import QuoRole, QuoTextChannel, checks

from .errors import SMError
from .events import ScrimEvents, Ssverification, TagEvents, TourneyEvents
from .helpers import delete_denied_message
from .slash import *
from .views import *


class ScrimManager(Cog, name="Esports"):
    def __init__(self, bot: Quotient):
        self.bot = bot

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

    @commands.command(aliases=("s", "sm"))
    @commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
    @commands.bot_has_guild_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    @commands.cooldown(1, 15, type=commands.BucketType.guild)
    async def smanager(self, ctx: Context):
        """
        Contains commands related to Quotient's powerful scrims manager.
        """
        if not any((ctx.author.guild_permissions.manage_guild, Scrim.is_ignorable(ctx.author))):
            return await ctx.error(f"You need `scrims-mod` role or `Manage-Server` permissions to use this command.")

        v = ScrimsMain(ctx)
        v.message = await ctx.send(embed=await v.initial_embed(), view=v)

    # ************************************************************************************************
    # ************************************************************************************************

    @commands.command(aliases=("tm", "t"))
    @commands.bot_has_permissions(embed_links=True, add_reactions=True, manage_messages=True)
    @commands.bot_has_guild_permissions(
        manage_channels=True, manage_permissions=True, manage_roles=True, manage_messages=True
    )
    @commands.cooldown(1, 15, type=commands.BucketType.guild)
    async def tourney(self, ctx: Context):
        """Create & Manage tournaments with Quotient"""
        if not Tourney.is_ignorable(ctx.author) and not ctx.author.guild_permissions.manage_guild:
            return await ctx.error(
                "You need either `Manage Server` permissions or `@tourney-mod` role to manage tournaments."
            )

        view = TourneyManager(ctx)
        view.add_item(QuotientView.tricky_invite_button())
        view.message = await ctx.send(embed=await view.initial_embed(), view=view)

    @commands.hybrid_command(
        aliases=("quickidp",),
        extras={"examples": ["idp 1234 pass Miramar", "idp 1234 pass Sanhok @role"]},
    )
    @commands.bot_has_permissions(embed_links=True, manage_messages=True)
    @checks.can_use_sm()
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
    async def idp(self, ctx: Context, room_id: str, password: str, map: str, role_to_ping: Optional[discord.Role] = None):
        """
        Share Id/pass with embed quickly.
        Message is automatically deleted after 30 minutes.
        """
        await ctx.message.delete(delay=0)
        room_id, password, map = truncate_string(room_id, 100), truncate_string(password, 100), truncate_string(map, 100)

        _e = discord.Embed(color=self.bot.color)
        _e.set_thumbnail(url=getattr(ctx.guild.icon, "url", self.bot.user.avatar.url))
        _e.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        _e.add_field(name="Room ID", value=room_id)
        _e.add_field(name="Password", value=password)
        _e.add_field(name="Map", value=map)
        _e.set_footer(text=f"Auto-delete time")
        _e.timestamp = self.bot.current_time + timedelta(minutes=30)

        view = IdpView(room_id, password, map)
        msg = await ctx.send(
            content=role_to_ping.mention if role_to_ping else None,
            embed=_e,
            view=view,
            allowed_mentions=discord.AllowedMentions(roles=True),
        )
        await self.bot.wait_and_delete(msg, 30 * 60)

    @commands.group(aliases=("eztag",), invoke_without_command=True)
    async def easytag(self, ctx: Context):
        """Commands related to quotient's eztag"""
        await ctx.send_help(ctx.command)

    @easytag.command(name="set", extras={"examples": ["eztag set #channel"]})
    # @checks.has_done_setup()
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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
                f"I need `send messages`, `embed links` and `manage messages` permission in {channel.mention}"
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

    @easytag.command(name="remove", extras={"examples": ["eztag remove #channel"]})
    # @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
    async def remove_eztag(self, ctx: Context, *, channel: QuoTextChannel):
        """Remove a eztag channel"""
        if not channel.id in self.bot.cache.eztagchannels:
            return await ctx.error(f"This is not a EasyTag channel.")

        await EasyTag.filter(channel_id=channel.id).delete()
        self.bot.cache.eztagchannels.discard(channel.id)
        await ctx.success(f"Removed {channel} from EasyTag channels.")

    @easytag.command(name="config")
    # @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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

    @easytag.command(name="autodelete", extras={"examples": ["eztag autodelete #channel"]})
    #    @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
    # @checks.has_done_setup()
    async def tagcheck_set(self, ctx: Context, channel: discord.TextChannel, mentions: int = 4):
        """
        Set a channel for tagcheck.
        mentions defines required mentions, It's 4 by default.
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
    # @checks.has_done_setup()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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

    @tagcheck.command(name="remove", extras={"examples": ["tagcheck remove #channel"]})
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
    async def tagcheck_remove(self, ctx: Context, *, channel: QuoTextChannel):
        """Remove a channel from tagcheck"""
        if not channel.id in self.bot.cache.tagcheck:
            return await ctx.error(f"This is not a TagCheck channel.")

        await TagCheck.filter(channel_id=channel.id).delete()
        self.bot.cache.tagcheck.discard(channel.id)
        await ctx.success(f"Removed {channel} from TagCheck channels.")

    @tagcheck.command(name="autodelete", extras={"examples": ["tagcheck autodelete #channel"]})
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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

    @commands.command(aliases=("slotm",))
    @checks.can_use_sm()
    @commands.bot_has_guild_permissions(embed_links=True, manage_messages=True, manage_channels=True)
    # # @checks.has_done_setup()
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
    async def slotmanager(self, ctx: Context):
        """
        SlotManager helps people to setup scrims-slots cancel and claim manager.
        Users can easily claim and cancel their slots anytime without bothering mods.
        """
        _view = ScrimsSlotManagerSetup(ctx)
        _e = await _view.initial_message(ctx.guild)
        _view.add_item(QuotientView.tricky_invite_button())
        _view.message = await ctx.send(embed=_e, view=_view, embed_perms=True)

    @commands.command(name="banlog", extras={"examples": ["banlog #channel"]})
    @checks.can_use_sm()
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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
    @commands.cooldown(1, 10, type=commands.BucketType.guild)
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


async def setup(bot: Quotient):
    await bot.add_cog(ScrimManager(bot))
    await bot.add_cog(SMError(bot))
    await bot.add_cog(ScrimEvents(bot))
    await bot.add_cog(TourneyEvents(bot))
    await bot.add_cog(TagEvents(bot))
    await bot.add_cog(Ssverification(bot))
    await bot.add_cog(SlotManagerEvents(bot))
    await bot.add_cog(SlashCog(bot))
