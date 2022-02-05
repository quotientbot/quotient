from __future__ import annotations

from typing import List, TYPE_CHECKING

import discord

from constants import SSType

if TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from utils import emote, plural

from core import Cog, Context
from models import SSVerify, SSData
from ..helpers.ssverify import valid_attachments, VerifyResult

from server.app.helpers._const import ImageResponse
import humanize


class Ssverification(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.request_url = self.bot.config.FASTAPI_URL + "/ocr"
        self.headers = {"authorization": self.bot.config.FASTAPI_KEY, "Content-Type": "application/json"}

    #         async with self.__verify_lock:
    #             _e = discord.Embed(title="", description="", color=self.color_bool([i.verified for i in _list]))

    #             for _ in _list:
    #                 _e.description += f"{record.emoji(_.verified)} | {_.reason}\n"

    #                 if _.verified:
    #                     data = await SSData.create(
    #                         author_id=ctx.author.id, channel_id=ctx.channel.id, message_id=ctx.message.id, hash=_.hash
    #                     )
    #                     await record.data.add(data)

    #             _e.set_footer(
    #                 text=f"Submitted {await record.data.filter(author_id=ctx.author.id).count()}/{record.required_ss}",
    #                 icon_url=getattr(ctx.author.avatar, "url", discord.Embed.Empty),
    #             )

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not all((message.guild, not message.author.bot, message.channel.id in self.bot.cache.ssverify_channels)):
            return

        record = await SSVerify.get_or_none(channel_id=message.channel.id)
        if not record:
            return self.bot.cache.ssverify_channels.discard(message.channel.id)

        if "tourney-mod" in (role.name.lower() for role in message.author.roles):
            return

        ctx: Context = await self.bot.get_context(message)

        _e = discord.Embed(color=discord.Color.red())

        with suppress(discord.HTTPException):
            if await record.is_user_verified(message.author.id):
                _e.description = "**Your screenshots are already verified, kindly move onto next step.**"
                return await ctx.reply(embed=_e)

            if not (attachments := valid_attachments(message)):
                _e.description = "**Kindly send screenshots in `png/jpg/jpeg` format only.**"
                return await ctx.reply(embed=_e)

            _e.color = discord.Color.yellow()
            _e.description = f"Processing your {plural(attachments):screenshot|screenshots}... {emote.loading}"
            m = await message.reply(embed=_e)

            _data = [{"url": _.proxy_url} for _ in attachments]

            _ocr, start_at = None, self.bot.current_time
            async with self.bot.session.post(self.request_url, json=_data, headers=self.headers) as resp:
                complete_at = self.bot.current_time
                _ocr = await resp.json()

            if not _ocr:
                return

            embed = await self.__verify_screenshots(record, [ImageResponse(**_) for _ in _ocr])
            embed.set_footer(text=f"Time taken: {humanize.precisedelta(complete_at-start_at)}")

            try:
                await m.delete()
            except discord.HTTPException:
                pass

            await message.reply(embed=_e)

            if await record.is_user_verified(ctx.author.id):
                _e.description = f"{ctx.author.mention} Your screenshots are verified, Move to next step."
                await message.reply(embed=_e)

                await message.author.add_roles(discord.Object(id=record.role_id))

                await message.author.send(
                    f"**Message from {message.guild.name} after ssverification**\n\n{record.success_message}"
                )

    async def __verify_screenshots(self, ctx: Context, record: SSVerify, _ocr: List[ImageResponse]) -> discord.Embed:
        _e = discord.Embed(color=self.bot.color, description="")

        for _ in _ocr:
            if record.ss_type == SSType.anyss:
                ...

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
