from __future__ import annotations

from discord.utils import escape_markdown
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog, Context
from discord.ext import commands
from models import Tag, AutoPurge
from ast import literal_eval as leval
from models import Autorole, ArrayAppend, ArrayRemove, Tag

from utils import (
    checks,
    ColorConverter,
    Pages,
    emote,
    strtime,
    plural,
    QuoRole,
    QuoMember,
    QuoCategory,
    QuoTextChannel,
    simple_convert,
)
from .functions import TagName, guild_tag_stats, increment_usage, TagConverter, is_valid_name, member_tag_stats
from contextlib import suppress
import discord
from io import BytesIO
import zipfile

from humanize import precisedelta
from datetime import timedelta

import asyncio
import config
import re


class Utility(Cog, name="utility"):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @checks.is_mod()
    async def autorole(self, ctx: Context, off: str = None):
        """
        Manage Quotient's autoroles.
        """
        if not off or not off.lower() == "off":
            return await ctx.send_help(ctx.command)

        record = await Autorole.get_or_none(guild_id=ctx.guild.id)

        if not record:
            return await ctx.send(
                f"You have not set any autorole yet.\n\nDo it like: `{ctx.prefix}autorole humans @role`"
            )

        elif not any([len(record.humans), len(record.bots)]):
            return await ctx.error("Autoroles already OFF!")

        else:
            prompt = await ctx.prompt("Are you sure you want to turn off autorole?")
            if prompt:
                # await Autorole.filter(guild_id=ctx.guild.id).update(humans=list, bots=list)
                await ctx.db.execute("UPDATE autoroles SET humans = '{}' , bots = '{}' WHERE guild_id = $1", ctx.guild.id)
                await ctx.success("Autoroles turned OFF!")
            else:
                await ctx.success("OK!")

    @autorole.command(name="humans")
    @checks.is_mod()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def autorole_humans(self, ctx: Context, *, role: QuoRole):
        """
        Add/ Remove a role to human autoroles.
        """
        record = await Autorole.get_or_none(pk=ctx.guild.id)
        if record is None:
            await Autorole.create(guild_id=ctx.guild.id, humans=[role.id])
            text = f"Added {role.mention} to human autoroles."

        else:
            func = (ArrayAppend, ArrayRemove)[role.id in record.humans]
            await Autorole.filter(guild_id=ctx.guild.id).update(humans=func("humans", role.id))
            text = (
                f"Added {role.mention} to human autoroles."
                if func == ArrayAppend
                else f"Removed {role.mention} from human autoroles."
            )

        await ctx.success(text)

    @autorole.command(name="bots")
    @checks.is_mod()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def autorole_bots(self, ctx: Context, *, role: QuoRole):
        """
        Add/ Remove a role to bot autoroles.
        """
        record = await Autorole.get_or_none(pk=ctx.guild.id)
        if record is None:
            await Autorole.create(guild_id=ctx.guild.id, bots=[role.id])
            text = f"Added {role.mention} to bot autoroles."

        else:
            func = (ArrayAppend, ArrayRemove)[role.id in record.bots]
            await Autorole.filter(guild_id=ctx.guild.id).update(bots=func("bots", role.id))
            text = (
                f"Added {role.mention} to bot autoroles."
                if func == ArrayAppend
                else f"Removed {role.mention} from bot autoroles."
            )

        await ctx.success(text)

    @autorole.command(name="config")
    @checks.is_mod()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def autorole_config(self, ctx: Context):
        """
        Get autorole config
        """
        record = await Autorole.get_or_none(pk=ctx.guild.id)
        if not record:
            return await ctx.send(
                f"You have not set any autorole yet.\n\nDo it like: `{ctx.prefix}autorole humans @role`"
            )

        humans = ", ".join(record.human_roles) if len(list(record.human_roles)) else "Not Set!"
        bots = ", ".join(record.bot_roles) if len(list(record.bot_roles)) else "Not Set!"

        embed = self.bot.embed(ctx, title="Autorole Config")
        embed.add_field(name="Humans", value=humans, inline=False)
        embed.add_field(name="Bots", value=bots, inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def firstmsg(self, ctx: Context, *, channel: discord.TextChannel = None):
        """Get the link to first message of current or any other channel."""
        channel = channel or ctx.channel
        messages = await channel.history(limit=1, oldest_first=True).flatten()
        return await ctx.send(f"Here's the link to first message of {channel.mention}:\n{messages[0].jump_url}")

    @commands.command(name="embed")
    @commands.has_permissions(manage_messages=True)
    async def embed_send(self, ctx: Context, channel: discord.TextChannel, color: ColorConverter, *, text: str):
        """
        Generated and sends embed to specified channel. Use qqe <message> for quick embeds
        Tip: You can send hyperlinks too. Example: `[anytext](any link)`
        """
        if not channel.permissions_for(ctx.me).embed_links:
            return await ctx.error(f"I need `embed_links` permission in {channel.mention}")

        embed = discord.Embed(color=color, description=text)
        if len(ctx.message.attachments) and "image" in ctx.message.attachments[0].content_type:
            embed.set_image(url=ctx.message.attachments[0].proxy_url)
        await ctx.send(embed=embed)
        prompt = await ctx.prompt(
            "Should I deliver it?",
        )

        if prompt:
            await channel.send(embed=embed)
            await ctx.success(f"Successfully delivered.")

        else:
            await ctx.success("Ok Aborting")

    @commands.command(name="quickembed", aliases=["qe"])
    @commands.has_permissions(manage_messages=True, embed_links=True)
    @commands.bot_has_permissions(manage_messages=True, embed_links=True)
    async def quick_embed_command(self, ctx: Context, *, text: str):
        """
        Generates quick embeds.
        Tip: You can send hyperlinks too. Example: `[anytext](any link)`
        """
        embed = self.bot.embed(ctx, description=text)
        if len(ctx.message.attachments) and "image" in ctx.message.attachments[0].content_type:
            embed.set_image(url=ctx.message.attachments[0].proxy_url)
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name="zipemojis")
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.max_concurrency(1, per=commands.BucketType.guild)
    async def zip_emojis(self, ctx: Context):
        """
        Get a zip file containing all the emojis in the current server.
        `Note:` This can take some time and you need to be patient.
        """

        if len(ctx.guild.emojis) == 0:
            return await ctx.error(f"Breh, Your server doesn't have any custom emojis.")

        m = await ctx.simple(
            f"Alright! Zipping all emojis owned by this server for you, This can take some time {emote.loading}"
        )
        buf = BytesIO()

        async with ctx.typing():
            with zipfile.ZipFile(buf, "w") as f:
                for emoji in ctx.guild.emojis:
                    _bytes = await emoji.url.read()
                    f.writestr(f'{emoji.name}.{"gif" if emoji.animated else "png"}', _bytes)

            buf.seek(0)

        try:
            await m.delete()
        except:
            pass
        finally:
            await ctx.send(
                f"{ctx.author.mention} Sorry to keep you waiting, here you go:",
                file=discord.File(fp=buf, filename="emojis.zip"),
            )

    # @commands.command()
    # @commands.bot_has_permissions(embed_links=True)
    # async def snipe(self, ctx, *, channel: Optional[discord.TextChannel]):
    #     """Snipe last deleted message of a channel."""

    #     channel = channel or ctx.channel

    #     snipe = await Snipes.filter(channel_id=channel.id).order_by("delete_time").first()
    #     if not snipe:
    #         return await ctx.send(f"There's nothing to snipe :c")

    #     elif snipe.nsfw and not channel.is_nsfw():
    #         return await ctx.send(f"The snipe is marked NSFW but the current channel isn't.")

    #     content = (
    #         snipe.content
    #         if len(snipe.content) < 128
    #         else f"[Click me to see]({str(await ctx.bot.binclient.post(snipe.content))})"
    #     )
    #     embed = self.bot.embed(ctx)
    #     embed.description = f"Message sent by **{snipe.author}** was deleted in {channel.mention}"
    #     embed.add_field(name="**__Message Content__**", value=content)
    #     embed.set_footer(text=f"Deleted {human_timedelta(snipe.delete_time)}")
    #     await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx: Context, *, name: TagConverter = None):
        """Call a tag with its name or id"""
        if name is None:
            return await ctx.send_help(ctx.command)

        if name.is_nsfw and not ctx.channel.is_nsfw():
            return await ctx.error("This tag can only be used in NSFW channels.")

        if name.is_embed is True:
            dict = leval(name.content)
            await ctx.send(embed=discord.Embed.from_dict(dict), reference=ctx.replied_reference)

        if not name.content:
            return await ctx.error(f"Tag doesn't have any content")
        else:
            await ctx.send(name.content, reference=ctx.replied_reference)
        await increment_usage(ctx, name.name)

    @tag.command(name="all", aliases=("list",))
    async def all_tags(self, ctx: Context, member: QuoMember = None):
        """Get all tags owned by the server or a member"""
        if not member:
            tags = await Tag.filter(guild_id=ctx.guild.id)

            if not len(tags):
                return await ctx.error("This server doesn't have any tags.")

        else:
            tags = await Tag.filter(guild_id=ctx.guild.id, owner_id=member.id)
            if not len(tags):
                return await ctx.error(f"{member} doesn't own any tag.")

        tag_list = []
        for idx, tag in enumerate(tags, start=1):
            tag_list.append(f"`{idx:02}` {escape_markdown(tag.name)} (ID: {tag.id})\n")

        paginator = Pages(
            ctx, title="Total tags: {}".format(len(tag_list)), entries=tag_list, per_page=12, show_entry_count=True
        )
        await paginator.paginate()

    @tag.command(name="info")
    async def tag_info(self, ctx: Context, *, tag: TagConverter):
        """Information about a tag"""
        embed = self.bot.embed(ctx, title=f"Stats for tag {tag.name}")

        user = self.bot.get_user(tag.owner_id) or await self.bot.fetch_user(tag.owner_id)

        embed.set_author(name=str(user), icon_url=user.avatar_url)

        embed.add_field(name="Owner", value=getattr(user, "mention", "Invalid User!"))
        embed.add_field(name="ID:", value=tag.id)
        embed.add_field(name="Uses", value=tag.usage)
        embed.add_field(name="NSFW", value="No" if not tag.is_nsfw else "Yes")
        embed.add_field(name="Embed", value="No" if not tag.is_embed else "Yes")
        embed.set_footer(text=f"Created At: {strtime(tag.created_at)}")
        await ctx.send(embed=embed)

    @tag.command(name="claim")
    async def claim_tag(self, ctx: Context, *, tag: TagConverter):
        """Claims a tag if the original owner left the server."""

        member = await self.bot.get_or_fetch_member(ctx.guild, tag.owner_id)

        if member is not None:
            return await ctx.send(f"The owner of this tag ({tag.owner}) is still in the server.")

        await Tag.filter(name=tag.name, guild_id=ctx.guild.id).update(owner_id=ctx.author.id)
        await ctx.success("Transfered tag ownership to you.")

    @tag.command(name="create")
    async def create_tag_command(self, ctx: Context, name: TagName, *, content=""):
        """Create a new tag"""

        if content == "" and not ctx.message.attachments:
            return await ctx.error("Cannot make an empty tag.")

        if len(ctx.message.attachments):
            content += f"\n{ctx.message.attachments[0].proxy_url}"

        if len(content) > 1990:
            return await ctx.error(f"Tag content cannot contain more than 1990 characters.")

        if len(name) > 99:
            return await ctx.error(f"Tag Name cannot contain more that 99 characters.")

        if await is_valid_name(ctx, name):
            tag = await Tag.create(name=name, content=content, guild_id=ctx.guild.id, owner_id=ctx.author.id)

            await ctx.success(f"Created Tag (ID: `{tag.id}`)")

        else:
            await ctx.error(f"Tag Name is already taken.")

    @tag.command(name="delete", aliases=["del"])
    async def delete_tag(self, ctx: Context, *, tag_name: TagConverter):
        """Delete a tag"""
        tag = tag_name
        if not tag.owner_id == ctx.author.id and not ctx.author.guild_permissions.manage_guild:
            return await ctx.error(f"This tag doesn't belong to you.")

        await Tag.filter(guild_id=ctx.guild.id, name=tag_name.name, owner_id=tag.owner_id).delete()
        await ctx.success(f"Deleted {tag_name.name}")

    @tag.command(name="transfer")
    async def transfer_tag(self, ctx: Context, member: QuoMember, *, tag: TagConverter):
        """Transfer the ownership of a tag."""

        if tag.owner_id != ctx.author.id:
            return await ctx.error(f"This tag doesn't belong to you.")

        await Tag.filter(id=tag.id).update(owner_id=member.id)
        await ctx.success("Transfer successful.")

    @tag.command("nsfw")
    async def nsfw_status_toggle(self, ctx: Context, *, tag: TagConverter):
        """Toggle NSFW for a tag."""
        if tag.owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_guild:
            return await ctx.error(f"This tag doesn't belong to you.")

        await Tag.filter(id=tag.id).update(is_nsfw=not (tag.is_nsfw))
        await ctx.success(f"Tag NSFW toggled {'ON' if not tag.is_nsfw else 'OFF'}!")

    @tag.command("mine")
    async def get_all_tags(self, ctx: Context):
        """Get a list of all tags owned by you."""
        tags = await Tag.filter(guild_id=ctx.guild.id, owner_id=ctx.author.id)

        tag_list = []
        for idx, tag in enumerate(tags, start=1):
            tag_list.append(f"`{idx:02}` {tag.name} (ID: {tag.id})\n")

        paginator = Pages(
            ctx, title="Tags you own: {}".format(len(tag_list)), entries=tag_list, per_page=12, show_entry_count=True
        )
        await paginator.paginate()

    @tag.command(name="purge")
    async def purge_tags(self, ctx: Context, member: QuoMember):
        """Delete all the tags of a member"""

        count = await Tag.filter(owner_id=member.id, guild_id=ctx.guild.id).count()
        if not count:
            return await ctx.error(f"{member} doesn't own any tag.")

        await Tag.filter(owner_id=member.id, guild_id=ctx.guild.id).delete()
        await ctx.success(f"Deleted {plural(count): tag|tags} of **{member}**.")

    @tag.command(name="edit")
    async def edit_tag(self, ctx: Context, name: TagName, *, content=""):
        """Edit a tag"""
        tag = await Tag.get_or_none(name=name, guild_id=ctx.guild.id)
        if not tag:
            return await ctx.error(f"Tag name is invalid.")

        if not tag.owner_id == ctx.author.id and not ctx.author.guild_permissions.manage_guild:
            return await ctx.error(f"This tag doesn't belong to you.")

        if len(content) > 1990:
            return await ctx.error(f"Tag content cannot exceed 1990 characters.")

        if content == "" and not ctx.message.attachments:
            return await ctx.error("Cannot edit tag.")

        if len(ctx.message.attachments):
            content += f"\n{ctx.message.attachments[0].proxy_url}"

        await Tag.filter(id=tag.id).update(content=content)
        await ctx.success(f"Tag updated.")

    # @tag.command(name="make")
    # async def tag_make(self, ctx: Context):
    #     """Make tags interactively."""

    #     def check(message: discord.Message):
    #         if message.content.strip().lower() == "cancel":
    #             raise commands.BadArgument("Alright, reverting all process.")

    #         return message.author == ctx.author and ctx.channel == message.channel

    #     msg = await ctx.simple("What do you want the tag name to be?")
    #     name = await inputs.string_input(ctx, check, delete_after=True)
    #     await inputs.safe_delete(msg)

    #     embed = await ctx.simple(
    #         f"What do you want the content to be?\n\n{keycap_digit(1)} | Simple Text\n{keycap_digit(2)} | Embed"
    #     )
    #     reactions = [keycap_digit(1), keycap_digit(2)]
    #     for reaction in reactions:
    #         await embed.add_reaction(reaction)

    @tag.command(name="search")
    async def search_tag(self, ctx: Context, *, name):
        """Search in all your tags."""
        tags = await Tag.filter(guild_id=ctx.guild.id, name__icontains=name)

        if not len(tags):
            return await ctx.error("No tags found.")

        tag_list = []
        for idx, tag in enumerate(tags, start=1):
            tag_list.append(f"`{idx:02}` {tag.name} (ID: {tag.id})\n")

        paginator = Pages(
            ctx, title="Matching Tags: {}".format(len(tag_list)), entries=tag_list, per_page=10, show_entry_count=True
        )
        await paginator.paginate()

    @tag.command(name="stats")
    async def tag_stats(self, ctx: Context, *, member: QuoMember = None):
        """Tag statistics of the server or a member."""
        if member:
            await member_tag_stats(ctx, member)
        else:
            await guild_tag_stats(ctx)

    @commands.group(invoke_without_command=True)
    async def category(self, ctx: Context):
        """hide , delete , unhide or even nuke a category"""
        await ctx.send_help(ctx.command)

    @category.command(name="delete")
    @commands.has_permissions(manage_channels=True, manage_guild=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def category_delete(self, ctx: Context, *, category: QuoCategory):
        """Delete a category and all the channels under it."""
        if not len(category.channels):
            return await ctx.error(f"**{category}** doesn't have any channels.")

        prompt = await ctx.prompt(
            message=f"All channels under the category `{category}` will be deleted.\nAre you sure you want to continue?"
        )
        if prompt:
            failed, success = 0, 0

            for channel in category.channels:
                try:
                    await channel.delete()
                    success += 1
                except:
                    failed += 1
                    continue

            await category.delete()

            with suppress(
                discord.Forbidden, commands.ChannelNotFound, discord.NotFound, commands.CommandInvokeError
            ):  # yes all these will be raised if the channel is from ones we deleted earlier.
                await ctx.success(f"Successfully deleted **{category}**. (Deleted: `{success}`, Failed: `{failed}`)")

        else:
            await ctx.simple(f"Ok Aborting.")

    @category.command(name="hide")
    @commands.has_permissions(manage_channels=True, manage_guild=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def category_hide(self, ctx: Context, *, category: QuoCategory):
        """Hide a category and all its channels"""
        if not len(category.channels):
            return await ctx.error(f"**{category}** doesn't have any channels.")

        prompt = await ctx.prompt(
            message=f"All channels under the category `{category}` will be hidden.\nAre you sure you want to continue?"
        )
        if prompt:
            failed, success = 0, 0

            for channel in category.channels:
                try:
                    perms = channel.overwrites_for(ctx.guild.default_role)
                    perms.read_messages = False
                    await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
                    success += 1
                except:
                    failed += 1
                    continue

            await ctx.success(f"Successfully hidden category. (Hidden: `{success}`, Failed: `{failed}`)")

        else:
            await ctx.simple("Ok Aborting.")

    @category.command(name="unhide")
    @commands.has_permissions(manage_channels=True, manage_guild=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def category_unhide(self, ctx: Context, *, category: QuoCategory):
        """Unhide a hidden category and all its channels."""
        if not len(category.channels):
            return await ctx.error(f"**{category}** doesn't have any channels.")

        prompt = await ctx.prompt(
            message=f"All channels under the category `{category}` will be unhidden.\nAre you sure you want to continue?"
        )
        if prompt:
            failed, success = 0, 0

            for channel in category.channels:
                try:
                    perms = channel.overwrites_for(ctx.guild.default_role)
                    perms.read_messages = True
                    await channel.set_permissions(ctx.guild.default_role, overwrite=perms)
                    success += 1
                except:
                    failed += 1
                    continue

            await ctx.success(f"Successfully unhidden **{category}**. (Unhidden: `{success}`, Failed: `{failed}`)")

        else:
            await ctx.simple("Ok Aborting.")

    @category.command(name="nuke")
    @commands.has_permissions(manage_channels=True, manage_guild=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def category_nuke(self, ctx: Context, *, category: QuoCategory):
        """
        Delete a category completely and create a new one
        This will delete all the channels under the category and will make a new one with same perms and channels.
        """
        if not len(category.channels):
            return await ctx.error(f"**{category}** doesn't have any channels.")

        prompt = await ctx.prompt(
            message=f"All channels under the category `{category}` will be cloned and deleted.\nAre you sure you want to continue?"
        )
        if prompt:
            failed, success = 0, 0
            for channel in category.channels:
                if channel.permissions_for(ctx.me).manage_channels:
                    try:
                        position = channel.position
                        clone = await channel.clone(reason=f"Action done by {ctx.author}")
                        await channel.delete()
                        await clone.edit(position=position)
                        success += 1

                    except:
                        failed += 1
                        continue

            await ctx.success(f"Successfully nuked **{category}**. (Cloned: `{success}`, Failed: `{failed}`)")

        else:
            await ctx.simple(f"Ok Aborting.")

    @commands.group(invoke_without_command=True)
    async def autopurge(self, ctx: Context):
        """
        Set Quotient to delete every new message in a channel after  a specific interval.
        """
        await ctx.send_help(ctx.command)

    @autopurge.command(name="set")
    @commands.has_permissions(manage_messages=True)
    async def autopurge_set(self, ctx: Context, channel: QuoTextChannel, delete_after):
        """
        Set the autopurge for a channel
        `delete_after` should be in this format: s|m|h|d
        """
        if not channel.permissions_for(ctx.me).manage_messages:
            return await ctx.error("I don't have `manage messages` permission in {0}".format(channel.mention))

        seconds = simple_convert(delete_after)

        if not seconds > 3 or seconds > 604800:
            return await ctx.error("Delete Time must be more than 3s and less than 7 days.")

        if (count := await AutoPurge.filter(guild_id=ctx.guild.id).count()) >= 1 and not await ctx.is_premium_guild():
            return await ctx.error(
                "You cannot set autopurge in more than 1 channel in free tier."
                f"\nHowever [Quotient Premium]({ctx.config.WEBSITE}/premium) allows you to set autopurge in unlimited channels."
            )

        if channel.id in self.bot.autopurge_channels:
            return await ctx.error(f"**{channel}** is already an autopurge channel.")

        await AutoPurge.create(guild_id=ctx.guild.id, channel_id=channel.id, delete_after=seconds)
        self.bot.autopurge_channels.add(channel.id)
        await ctx.success(f"**{channel}** added to autopurge channels.")

    @autopurge.command(name="list")
    @commands.has_permissions(manage_messages=True)
    async def autopurge_config(self, ctx: Context):
        """Get a list of all autopurge channels"""
        records = await AutoPurge.filter(guild_id=ctx.guild.id)
        if not records:
            return await ctx.error("This server doesn't have any autopurge channels.")

        text = ""
        for idx, record in enumerate(records, start=1):
            text += f"`{idx:02}` | {getattr(record.channel, 'mention','Deleted Channel')} ({precisedelta(timedelta(seconds= record.delete_after))})\n"

        await ctx.send(embed=self.bot.embed(ctx, description=text, title="AutoPurge List"), embed_perms=True)

    @autopurge.command(name="remove")
    @commands.has_permissions(manage_messages=True)
    async def autopurge_remove(self, ctx: Context, *, channel: QuoTextChannel):
        """Remove a channel from autopurge"""
        if not channel.id in self.bot.autopurge_channels:
            return await ctx.error(f"{channel} is not an autopurge channel.")

        self.bot.autopurge_channels.discard(channel.id)
        await AutoPurge.filter(channel_id=channel.id, guild_id=ctx.guild.id).delete()
        await ctx.success(f"**{channel}** removed from autopurge channels.")


def setup(bot) -> None:
    bot.add_cog(Utility(bot))
