from __future__ import annotations
import asyncio

from typing import List, TYPE_CHECKING
import aiohttp

import discord

from constants import SSType

if TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from utils import emote, plural

from core import Cog, Context, QuotientRatelimiter
from models import SSVerify, ImageResponse

import humanize
from collections import defaultdict


class MemberLimits(defaultdict):
    def __missing__(self, key):
        r = self[key] = QuotientRatelimiter(1, 7)
        return r


class GuildLimits(defaultdict):
    def __missing__(self, key):
        r = self[key] = QuotientRatelimiter(10, 60)
        return r


class Ssverification(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.request_url = self.bot.config.FASTAPI_URL + "/ocr"
        self.headers = {"authorization": self.bot.config.FASTAPI_KEY, "Content-Type": "application/json"}

        self.__mratelimiter = MemberLimits(QuotientRatelimiter)  # ss/15s by member
        self.__gratelimiter = GuildLimits(QuotientRatelimiter)  # ss/minute by guild
        self.__verify_lock = asyncio.Lock()

    async def __check_ratelimit(self, message: discord.Message):
        if retry := self.__mratelimiter[message.author].is_ratelimited(message.author):
            await message.reply(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=f"**You are too fast. Kindly resend after `{retry:.2f}` seconds.**",
                )
            )
            return False

        elif retry := self.__gratelimiter[message.guild].is_ratelimited(message.guild):
            await message.reply(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=f"**Many users are submitting screenshots from this server at this time. Kindly retry after `{retry:.2f}` seconds.**",
                )
            )
            return False
        return True

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if not all((message.guild, not message.author.bot, message.channel.id in self.bot.cache.ssverify_channels)):
            return

        record = await SSVerify.get_or_none(channel_id=message.channel.id)
        if not record:
            return self.bot.cache.ssverify_channels.discard(message.channel.id)
        #
        if "tourney-mod" in (role.name.lower() for role in message.author.roles):
            return

        ctx: Context = await self.bot.get_context(message)

        _e = discord.Embed(color=discord.Color.red())

        with suppress(discord.HTTPException):
            if await record.is_user_verified(message.author.id):
                _e.description = "**Your screenshots are already verified, kindly move onto next step.**"
                return await ctx.reply(embed=_e)

            if not (attachments := self.__valid_attachments(message)):
                _e.description = "**Kindly send screenshots in `png/jpg/jpeg` format only.**"
                return await ctx.reply(embed=_e)

            if not await self.__check_ratelimit(message):
                return

            if len(attachments) > record.required_ss:
                _e.description = (
                    f"**You only have to send `{record.required_ss}` screenshots but you sent `{len(attachments)}`**"
                )
                return await ctx.reply(embed=_e)

            _e.color = discord.Color.yellow()
            _e.description = f"Processing your {plural(attachments):screenshot|screenshots}... {emote.loading}"
            m = await message.reply(embed=_e)

            _data = [{"url": _.proxy_url} for _ in attachments]

            start_at = self.bot.current_time

            async with self.__verify_lock:
                async with self.bot.session.post(self.request_url, json=_data, headers=self.headers) as resp:
                    complete_at = self.bot.current_time

                    try:
                        _ocr = await resp.json()
                    except aiohttp.ContentTypeError:
                        _e.color, _e.description = (
                            discord.Color.red(),
                            "**Failed to process your screenshots. Try again later.**",
                        )
                        return await message.reply(embed=_e)

            embed = await self.__verify_screenshots(ctx, record, [ImageResponse(**_) for _ in _ocr])
            embed.set_footer(text=f"Time taken: {humanize.precisedelta(complete_at-start_at)}")
            embed.set_author(
                name=f"Submitted {await record.data.filter(author_id=ctx.author.id).count()}/{record.required_ss}",
                icon_url=getattr(ctx.author.display_avatar, "url", discord.Embed.Empty),
            )

            with suppress(discord.HTTPException):
                await m.delete()

            await message.reply(embed=embed)

            if await record.is_user_verified(ctx.author.id):
                await message.author.add_roles(discord.Object(id=record.role_id))

                if record.success_message:
                    _e.title = f"Screenshot Verification Complete"
                    _e.url, _e.description = message.jump_url, record.success_message

                    return await message.reply(embed=_e)

                _e.description = f"{ctx.author.mention} Your screenshots are verified, Move to next step."
                await message.reply(embed=_e)

    async def __verify_screenshots(self, ctx: Context, record: SSVerify, _ocr: List[ImageResponse]) -> discord.Embed:
        _e = discord.Embed(color=self.bot.color, description="")

        for _ in _ocr:
            if not record.allow_same:
                b, t = await record._match_for_duplicate(_.dhash, _.phash, ctx.author.id)
                if b:
                    _e.description += t
                    continue

            if record.ss_type == SSType.anyss:
                _e.description += f"{record.emoji(True)} | Successfully Verified.\n"
                await record._add_to_data(ctx, _)

            elif record.ss_type == SSType.yt:
                _e.description += await record.verify_yt(ctx, _)

            elif record.ss_type == SSType.insta:
                _e.description += await record.verify_insta(ctx, _)

            elif record.ss_type == SSType.loco:
                _e.description += await record.verify_loco(ctx, _)

            elif record.ss_type == SSType.rooter:
                _e.description += await record.verify_rooter(ctx, _)

            elif record.ss_type == SSType.custom:
                _e.description += await record.verify_custom(ctx, _)

        return _e

    def __valid_attachments(self, message: discord.Message):
        return [_ for _ in message.attachments if _.content_type in ("image/png", "image/jpeg", "image/jpg")]

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
