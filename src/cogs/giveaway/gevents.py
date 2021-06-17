from cogs.giveaway.functions import check_giveaway_requirements, confirm_entry, end_giveaway, refresh_giveaway
from datetime import datetime, timedelta
from core import Cog, Context, Quotient
from models import Timer, Giveaway, ArrayRemove
from contextlib import suppress
from discord.ext import tasks
from constants import IST
import discord


class Gevents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.giveaway_refresher.start()
        self.bot.loop.create_task(self.delete_older_giveaways())

    def cog_unload(self):
        self.giveaway_refresher.stop()

    async def delete_older_giveaways(self):
        await Giveaway.filter(ended_at__lte=(datetime.now(tz=IST) - timedelta(hours=24))).delete()

    @tasks.loop(seconds=10)
    async def giveaway_refresher(self):
        records = await Giveaway.filter(ended_at__isnull=True, end_at__gte=datetime.now(tz=IST) + timedelta(seconds=5))
        if records:
            for record in records:
                await refresh_giveaway(record)

    @giveaway_refresher.before_loop
    async def refresher_before_loop(self):
        await self.bot.wait_until_ready()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return

        if payload.user_id == self.bot.user.id:
            return

        giveaway = await Giveaway.get_or_none(message_id=payload.message_id)
        if not giveaway:
            return

        if not giveaway.started_at or giveaway.ended_at:
            return

        msg = giveaway.message
        guild = giveaway._guild

        member = guild.get_member(payload.user_id)
        if not member:
            return

        if not payload.emoji.name == "🎉":
            with suppress(discord.HTTPException, discord.NotFound, AttributeError, discord.Forbidden):
                await msg.remove_reaction(payload.emoji, member=member)

        if member.id in giveaway.participants:  # smh there are already in the participants list
            return

        _bool = await check_giveaway_requirements(giveaway, member)
        if not _bool:
            return

        await confirm_entry(giveaway, member)

    @Cog.listener()
    async def on_giveaway_timer_complete(self, timer: Timer):
        message_id = timer.kwargs["message_id"]

        giveaway = await Giveaway.get_or_none(message_id=message_id)
        if not giveaway:
            return

        channel = giveaway.channel
        if not channel:
            return await Giveaway.filter(message_id=message_id).delete()

        if giveaway.ended_at:  # someone already ended it manually
            return

        await end_giveaway(giveaway)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        giveaway = await Giveaway.get_or_none(message_id=payload.message_id)
        if not giveaway:
            return

        if giveaway.ended_at:
            return

        if payload.user_id in giveaway.participants:
            await Giveaway.filter(message_id=payload.message_id).update(
                participants=ArrayRemove("participants", payload.user_id)
            )

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await Giveaway.filter(channel_id=channel.id).delete()

    @Cog.listener()
    async def on_raw_message_delete(self, payload):
        await Giveaway.filter(message_id=payload.message_id).delete()
