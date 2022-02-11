from contextlib import suppress
from discord.ext import commands
import discord, asyncio

import utils, io

from async_property import async_property

import config as cfg


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        from .Bot import Quotient

        self.bot: Quotient

    @property
    def db(self):
        return self.bot.db

    @property
    def session(self):
        return self.bot.session

    @property
    def guild_color(self):
        return self.bot.cache.guild_color(self.guild.id)

    @property
    def config(self) -> cfg:
        return self.bot.config

    @async_property
    async def banlog_channel(self):
        from models import BanLog

        record = await BanLog.get_or_none(guild_id=self.guild.id)
        if record:
            return record.channel

    @discord.utils.cached_property
    def replied_reference(self):
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    async def prompt(self, message, title=None, delete_after=True):
        """
        An interactive reaction confirmation dialog.
        """

        embed = discord.Embed(description=message, color=self.bot.color)
        if title is not None:
            embed.title = title

        view = utils.Prompt(self.author.id)
        msg = await self.send(embed=embed, view=view)
        await view.wait()

        try:
            if delete_after:
                await msg.delete()
        finally:
            return view.value

    async def error(self, message, delete_after=None, **kwargs):
        with suppress(discord.HTTPException):

            return await self.reply(
                embed=discord.Embed(description=message, color=discord.Color.red()),
                delete_after=delete_after,
                **kwargs,
            )

    async def safe_delete(self, msg: discord.Message, sleep_for: int = 0):
        if sleep_for:
            await asyncio.sleep(sleep_for)

        with suppress(discord.NotFound, discord.Forbidden):
            await msg.delete()

    async def success(self, message, delete_after=None, **kwargs):
        with suppress(discord.HTTPException):
            return await self.reply(
                embed=discord.Embed(
                    description=f"{utils.check} | {message}",
                    color=self.bot.color,
                ),
                delete_after=delete_after,
                **kwargs,
            )

    async def simple(self, message, delete_after=None, **kwargs):
        with suppress(discord.HTTPException):

            return await self.reply(
                embed=discord.Embed(
                    description=message,
                    color=self.bot.color,
                ).set_image(url=kwargs.get("image", discord.Embed.Empty)),
                delete_after=delete_after,
                **kwargs,
            )

    async def is_premium_guild(self):
        from models import Guild

        with suppress(AttributeError):
            return (await Guild.get(guild_id=self.guild.id)).is_premium

    async def send_file(self, content, *, name: str = "Message.txt", escape_mentions=True, **kwargs):
        """
        sends the file containg content
        """
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        fp = io.BytesIO(content.encode())
        kwargs.pop("file", None)

        return await self.send(file=discord.File(fp, filename=name), **kwargs)

    async def maybe_delete(self, message):
        with suppress(AttributeError, discord.NotFound, discord.Forbidden):
            await message.delete()

    async def send(self, content: any = None, **kwargs):
        if not (_perms := self.channel.permissions_for(self.me)).send_messages:
            try:
                await self.author.send(
                    "I can't send any messages in that channel. \nPlease give me sufficient permissions to do so."
                )
            except discord.Forbidden:
                pass
            return

        require_embed_perms = kwargs.pop("embed_perms", False)
        if require_embed_perms and not _perms.embed_links:
            kwargs = {}
            content = (
                "Oops! I need **Embed Links** permission to work properly. \n"
                "Please tell a server admin to grant me that permission."
            )
        if isinstance(content, discord.Embed):
            kwargs["embed"] = content
            content = None
        if isinstance(content, discord.File):
            kwargs["file"] = content
            content = None

        return await super().send(content, **kwargs)

    async def wait_and_purge(self, channel, *, limit=100, wait_for=10, check=lambda m: True):
        await asyncio.sleep(wait_for)

        with suppress(discord.HTTPException):
            await channel.purge(limit=limit, check=check)

    async def premium_mango(self, msg="*This feature requires you to have Quotient Premium.*"):
        from cogs.premium.views import PremiumView

        _view = PremiumView(msg)
        await self.send(embed=_view.premium_embed, view=_view, embed_perms=True)
