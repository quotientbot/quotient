from models import EasyTag, TagCheck, Scrim, AssignedSlot, ArrayRemove
from core import Quotient, Cog
from .utils import delete_denied_message, scrim_end_process, add_role_and_reaction
from .converters import EasyMemberConverter
from contextlib import suppress
import discord, asyncio
import utils
import re

from typing import NamedTuple

QueueMessage = NamedTuple("QueueMessage", [("scrim", Scrim), ("message", discord.Message)])


class ScrimEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.scrim_queue = asyncio.Queue()
        self.tourney_queue = asyncio.Queue()

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
