from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from io import BytesIO

import discord
from aiohttp import ContentTypeError, FormData
from discord.ext import commands
from humanize import precisedelta

from quotient.lib import CROSS, LOADING, TICK, plural
from quotient.models.esports.ssverify import ScreenshotType, SSverify, SSverifyEntry


class SSverifyEvents(commands.Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

        self.ocr_server_uri: str = "http://ocr:8080/"

    async def verify_youtube_ss(self, record: SSverify, message: discord.Message, resp: dict):
        og_txt = resp["text"]
        txt_lower = og_txt.lower().strip().replace(" ", "")

        if not any(_ in txt_lower for _ in ("subscribe", "videos")):
            return f"{CROSS} | This is not a valid youtube screenshot.\n"

        elif not record.entity_name.lower().replace(" ", "") in txt_lower:
            return f"{CROSS} | Screenshot must belong to [`{record.entity_name}`]({record.default_entity_link}) channel.\n"

        elif not "subscribed" in txt_lower:
            return f"{CROSS} | You must subscribe [`{record.entity_name}`]({record.default_entity_link}) to get verified.\n"

        await SSverifyEntry.create(
            ssverify=record,
            author_id=message.author.id,
            channel_id=record.channel_id,
            message_id=message.id,
            dHash=resp["dHash"][2:],
        )

        return f"{TICK} | Verified successfully.\n"

    async def verify_instagram_ss(self, record: SSverify, message: discord.Message, resp: dict):
        og_txt = resp["text"]
        txt_lower = og_txt.lower().strip().replace(" ", "")

        if not any(_ in txt_lower for _ in ("follow", "followers")):
            return f"{CROSS} | This is not a valid instagram screenshot.\n"

        elif not record.entity_name.lower().replace(" ", "") in txt_lower:
            return f"{CROSS} | Screenshot must belong to [`{record.entity_name}`]({record.default_entity_link}) profile.\n"

        elif not "following" in txt_lower:
            return f"{CROSS} | You must follow [`{record.entity_name}`]({record.default_entity_link}) to get verified.\n"

        await SSverifyEntry.create(
            ssverify=record,
            author_id=message.author.id,
            channel_id=record.channel_id,
            message_id=message.id,
            dHash=resp["dHash"][2:],
        )

        return f"{TICK} | Verified successfully.\n"

    async def verify_custom_ss(self, record: SSverify, message: discord.Message, resp: dict): ...

    async def validate_and_resp(self, record: SSverify, message: discord.Message, ocr_result: list[dict]) -> discord.Embed:
        e = discord.Embed(color=self.bot.color, description="")

        for res in ocr_result:
            if not record.allow_duplicate_ss:
                is_duplicate, text = await record.check_duplicate_ss(res["dHash"], message.author.id)
                if is_duplicate:
                    e.description += text
                    continue

            if record.screenshot_type == ScreenshotType.ANY:
                e.description += f"{TICK} | Successfully Verified.\n"

            elif record.screenshot_type == ScreenshotType.YT:
                e.description += await self.verify_youtube_ss(record, message, res)

            elif record.screenshot_type == ScreenshotType.INSTA:
                e.description += await self.verify_instagram_ss(record, message, res)

            elif record.screenshot_type == ScreenshotType.CUSTOM:
                e.description += await self.verify_custom_ss(record, message, res)

        return e

    @commands.Cog.listener(name="on_message")
    async def on_ssverify_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if not message.channel.id in self.bot.cache.ssverify_channel_ids:
            return

        record = await SSverify.get_or_none(channel_id=message.channel.id).prefetch_related("entries")
        if not record:
            return self.bot.cache.ssverify_channel_ids.discard(message.channel.id)

        valid_attachments = [a for a in message.attachments if a.filename.endswith((".png", ".jpg", ".jpeg"))]
        if "tourney-mod" in (role.name.lower() for role in message.author.roles):
            return

        e = discord.Embed(color=discord.Color.red())
        if not valid_attachments:
            e.description = f"`Hey {message.author}, Kindly send screenshots in 'png/jpg/jpeg' format only`"
            return await message.reply(embed=e)

        if sum(1 for i in record.entries if i.author_id == message.author.id) >= record.required_ss:
            e.description = f"`Hey {message.author}, You have already submitted the required number of screenshots.`"
            if record.success_message:
                e.description += f"\n\nMessage from Server Admin:\n{record.success_message}"

            return await message.reply(embed=e)

        if len(valid_attachments) > record.required_ss:
            e.description = f"`Hey {message.author}, You can only submit {record.required_ss} screenshots at a time.`"
            return await message.reply(embed=e)

        e.color = discord.Color.yellow()
        e.description = f"Processing your {plural(valid_attachments):screenshot|screenshots}... {LOADING}"
        processing_msg = await message.reply(embed=e)

        form_data = FormData()
        for img in valid_attachments:
            form_data.add_field("images", BytesIO(await img.read()), filename=img.filename, content_type=img.content_type)

        self.bot.logger.debug(f"Sending request to OCR server for {len(valid_attachments)} screenshots.")
        start_at = self.bot.current_time
        async with self.bot.session.post(self.ocr_server_uri, data=form_data) as resp:
            complete_at = self.bot.current_time
            self.bot.logger.debug(f"Received response from OCR server for {len(valid_attachments)} screenshots. {resp.status}")
            if not resp.status == 200:
                e.color = discord.Color.red()
                e.description = f"`Hey {message.author}, Unfortunately an error occurred while processing your screenshots. Please try again after some time.`"
                return await processing_msg.edit(embed=e)

            try:
                data = await resp.json()
            except ContentTypeError:
                e.color = discord.Color.red()
                e.description = f"`Hey {message.author}, Unfortunately an error occurred while processing your screenshots. Please try again after some time.`"
                return await processing_msg.edit(embed=e)

        e = await self.validate_and_resp(record, message, data)
        author_submitted = await record.entries.filter(author_id=message.author.id).count()

        e.set_footer(text=f"Time taken: {precisedelta(complete_at-start_at)}")
        e.set_author(
            name=f"Submitted {author_submitted}/{record.required_ss}",
            icon_url=getattr(message.author.display_avatar, "url", None),
        )
        try:
            await processing_msg.edit(embed=e)
        except discord.NotFound:
            await message.reply(embed=e)

        if author_submitted >= record.required_ss:
            await message.author.add_roles(discord.Object(id=record.role_id))

            e = discord.Embed(
                color=self.bot.color,
                title="Screenshot Verification Complete",
                description=f"{message.author.mention} Your screenshots are now verified.",
                url=message.jump_url,
            )

            if record.success_message:
                e.description += f"\n\nMessage from Server Admin:\n{record.success_message}"

            await message.reply(embed=e)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        if channel.id in self.bot.cache.ssverify_channel_ids:
            record = await SSverify.get_or_none(channel_id=channel.id)
            if record:
                await record.full_delete()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        records = await SSverify.filter(role_id=role.id)
        if records:
            for record in records:
                await record.full_delete()


async def setup(bot: Quotient):
    await bot.add_cog(SSverifyEvents(bot))
