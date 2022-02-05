from __future__ import annotations

import typing

import discord

if typing.TYPE_CHECKING:
    from core import Quotient

import asyncio

from contextlib import suppress
from utils import emote, plural

from core import Cog, Context
from models import SSVerify, SSData
from ..helpers.ssverify import get_image, verify_image, valid_attachments, VerifyResult


class Ssverification(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.__verify_lock = asyncio.Lock()

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not all((message.guild, not message.author.bot, message.channel.id in self.bot.cache.ssverify_channels)):
            return

        record = await SSVerify.get_or_none(channel_id=message.channel.id)
        if not record:
            self.bot.cache.ssverify_channels.discard(message.channel.id)

        if "tourney-mod" in (role.name.lower() for role in message.author.roles):
            return

        ctx: Context = await self.bot.get_context(message)

        with suppress(discord.HTTPException):
            if await record.is_user_verified(message.author.id):
                return await ctx.simple("**Your screenshots are already verified, kindly move onto next step.**")

            if not (attachments := valid_attachments(message)):
                return await ctx.error("**Kindly send screenshots in `png/jpg/jpeg` format only.**")

            m = await message.reply(
                embed=discord.Embed(
                    color=discord.Color.yellow(),
                    description=f"Processing your {plural(attachments):screenshot|screenshots}... {emote.loading}",
                )
            )

            _list: typing.List[VerifyResult] = []

            for _att in attachments:
                img = await get_image(_att)

                _list.append(await verify_image(record, img))

            async with self.__verify_lock:
                _e = discord.Embed(title="", description="", color=self.color_bool([i.verified for i in _list]))

                for _ in _list:
                    _e.description += f"{record.emoji(_.verified)} | {_.reason}\n"

                    if _.verified:
                        data = await SSData.create(
                            author_id=ctx.author.id, channel_id=ctx.channel.id, message_id=ctx.message.id, hash=_.hash
                        )
                        await record.data.add(data)

                _e.set_footer(
                    text=f"Submitted {await record.data.filter(author_id=ctx.author.id).count()}/{record.required_ss}",
                    icon_url=getattr(ctx.author.avatar, "url", discord.Embed.Empty),
                )

                try:
                    await m.delete()
                except discord.HTTPException:
                    pass

                await message.reply(embed=_e)

                if await record.is_user_verified(ctx.author.id):
                    await ctx.success(f"{ctx.author.mention} Your screenshots are verified, Move to next step.")

                    await message.author.add_roles(discord.Object(id=record.role_id))
                    await message.author.send(
                        f"**Message from {message.guild.name} after ssverification**\n\n{record.success_message}"
                    )

    def color_bool(self, colors: typing.List[bool]):
        _t, _f = sum(1 for _ in colors if _), sum(1 for _ in colors if not _)

        if _t == _f:
            return discord.Color.yellow()

        elif _t > _f:
            return discord.Color.green()

        else:
            return discord.Color.red()

    # @Cog.listener()
    # async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
    #     ...

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        if channel.id in self.bot.cache.ssverify_channels:
            record = await SSVerify.get_or_none(channel_id=channel.id)
            if record:
                await record.full_delete()

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        records = await SSVerify.filter(role_id=role.id)
        if records:
            for record in records:
                await record.full_delete()
