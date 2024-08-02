from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from datetime import timedelta

import discord
from core import Context
from discord.ext import commands, tasks
from tortoise.expressions import Q

from quotient.models import AutoPurge, Snipe, Timer, YtNotification

from .views import AutopurgeView, YtNotificationView


class Utility(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.bot.loop.create_task(self.delete_older_snipes())
        self.resub_yt_notifiers.start()

    def cog_unload(self):
        self.resub_yt_notifiers.stop()

    async def delete_older_snipes(self):  # we delete snipes that are older than 10 days
        await self.bot.wait_until_ready()
        await Snipe.filter(deleted_at__lte=(self.bot.current_time - timedelta(days=10))).delete()

    @commands.Cog.listener(name="on_message_delete")
    async def on_new_snipe_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        channel = message.channel
        if not channel.type in (
            discord.ChannelType.text,
            discord.ChannelType.private_thread,
            discord.ChannelType.public_thread,
        ):
            return

        content = message.content

        if not content or content.isspace():
            return

        await Snipe.update_or_create(
            channel_id=channel.id,
            defaults={
                "author_id": message.author.id,
                "content": content,
                "nsfw": channel.is_nsfw(),
            },
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        if channel.id in self.bot.cache.autopurge_channel_ids:
            await AutoPurge.filter(channel_id=channel.id).delete()
            self.bot.cache.autopurge_channel_ids.discard(channel.id)

    @commands.Cog.listener(name="on_message")
    async def on_autopurge_message(self, message: discord.Message):
        if not message.channel.id in self.bot.cache.autopurge_channel_ids:
            return

        record = await AutoPurge.get_or_none(channel_id=message.channel.id)
        if not record:
            return self.bot.cache.autopurge_channel_ids.discard(message.channel.id)

        await self.bot.reminders.create_timer(
            self.bot.current_time + timedelta(seconds=record.delete_after),
            "autopurge",
            message_id=message.id,
            channel_id=message.channel.id,
        )

    @commands.Cog.listener()
    async def on_autopurge_timer_complete(self, timer: Timer):
        message_id, channel_id = timer.kwargs["message_id"], timer.kwargs["channel_id"]

        record = await AutoPurge.get_or_none(channel_id=channel_id)
        if not record:
            return

        channel = record.channel
        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
            if message and not message.pinned:
                await message.delete(delay=0, reason="AutoPurge is on this channel.")
        except discord.HTTPException:
            pass

    @tasks.loop(seconds=10)
    async def resub_yt_notifiers(self):
        async for record in YtNotification.filter(lease_ends_at__lte=(self.bot.current_time + timedelta(minutes=10))):
            await record.setup_or_resubscribe()

    @commands.hybrid_command(name="yt-notifier", aliases=["yt"])
    async def yt_notifier(self, ctx: Context):
        """
        Setup notifications for new videos and live streams.
        """
        v = YtNotificationView(ctx)
        v.message = await ctx.send(embed=await v.initial_msg(), view=v)

    @commands.hybrid_command(name="autopurge", aliases=["ap"])
    async def autopurge_cmd(self, ctx: Context):
        """
        Autopurge allows you to set a time after which every new message in the channel will be deleted.
        """
        v = AutopurgeView(self.bot, ctx)
        v.message = await ctx.send(embed=await v.initial_msg(), view=v)

    @commands.hybrid_command(name="snipe")
    async def snipe(self, ctx: Context, channel: discord.TextChannel = None):
        """
        Sneaky way to see last deleted message of a channel.
        """
        channel = channel or ctx.channel

        snipe = await Snipe.filter(channel_id=channel.id).order_by("-deleted_at").first()

        if not snipe:
            return await ctx.send(embed=self.bot.error_embed("Nothing to snipe here!"), ephemeral=True)

        elif snipe.nsfw and not ctx.channel.is_nsfw():
            return await ctx.send(
                embed=self.bot.error_embed("This snipe is NSFW, please use an NSFW channel!"),
                ephemeral=True,
            )

        embed = discord.Embed(
            color=self.bot.color,
            timestamp=snipe.deleted_at,
        )
        embed.set_author(
            name=snipe.author,
            icon_url=snipe.author.display_avatar.url if snipe.author else None,
        )
        embed.description = f"{discord.utils.format_dt(snipe.deleted_at)}\n" f"\n**__Deleted Message Content__**\n{snipe.content}"

        embed.set_footer(text="Deleted")
        await ctx.send(embed=embed)


async def setup(bot: Quotient):
    await bot.add_cog(Utility(bot))
