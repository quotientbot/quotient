from __future__ import annotations

import asyncio
import io
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, TypeVar, Union

import aiohttp
import config as cfg
import discord
import utils
from async_property import async_property
from discord.ext import commands

BotT = TypeVar("BotT", bound=commands.Bot)


__all__ = ("Context",)


class Context(commands.Context["commands.Bot"], Generic[BotT]):

    if TYPE_CHECKING:
        from .Bot import Quotient

    bot: Quotient

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    @property
    def db(self):
        return self.bot.db

    @property
    def session(self) -> aiohttp.ClientSession:
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
    def replied_reference(self) -> Optional[discord.MessageReference]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    async def prompt(self, message: str, title: Optional[str] = None, delete_after=True):
        """
        An interactive reaction confirmation dialog.
        """

        embed = discord.Embed(description=message, color=self.bot.color)
        if title is not None:
            embed.title = title

        view = utils.Prompt(self.author.id)
        msg: Optional[discord.Message] = await self.send(embed=embed, view=view)
        await view.wait()

        try:
            if delete_after and msg is not None:
                await msg.delete(delay=0)
        finally:
            return view.value

    async def error(self, message: str, delete_after: bool = None, **kwargs: Any) -> Optional[discord.Message]:
        with suppress(discord.HTTPException):

            msg: Optional[discord.Message] = await self.reply(
                embed=discord.Embed(description=message, color=discord.Color.red()),
                delete_after=delete_after,
                **kwargs,
            )
            try:
                await self.bot.wait_for("message_delete", check=lambda m: m.id == self.message.id, timeout=30)
            except asyncio.TimeoutError:
                pass
            else:
                if msg is not None:
                    await msg.delete(delay=0)
            finally:
                return msg

        return None

    async def safe_delete(self, msg: discord.Message, sleep_for: Union[int, float] = 0) -> None:
        if sleep_for:
            await asyncio.sleep(sleep_for)

        await msg.delete(delay=0)

    async def success(
        self, message: str, delete_after: Union[int, float] = None, **kwargs: Any
    ) -> Optional[discord.Message]:
        with suppress(discord.HTTPException):
            return await self.reply(
                embed=discord.Embed(
                    description=f"{utils.check} | {message}",
                    color=self.bot.color,
                ),
                delete_after=delete_after,
                **kwargs,
            )
        return None

    async def simple(
        self, message: str, delete_after: Union[int, float] = None, **kwargs: Any
    ) -> Optional[discord.Message]:
        with suppress(discord.HTTPException):
            image = kwargs.pop("image", None)
            footer = kwargs.pop("footer", None)

            embed = discord.Embed(description=message, color=self.bot.color)
            if image:
                embed.set_image(url=image)
            if footer:
                embed.set_footer(text=footer)

            return await self.reply(
                embed=embed,
                delete_after=delete_after,
                **kwargs,
            )
        return None

    async def is_premium_guild(self) -> bool:
        from models import Guild

        with suppress(AttributeError):
            return (await Guild.get(guild_id=self.guild.id)).is_premium

        return False

    async def send_file(
        self,
        content: str,
        *,
        name: str = "Message.txt",
        escape_mentions: bool = True,
        **kwargs: Any,
    ) -> Optional[discord.Message]:
        """sends the file containg content"""
        if escape_mentions:
            content = discord.utils.escape_mentions(content)

        fp = io.BytesIO(content.encode())
        kwargs.pop("file", None)

        return await self.send(file=discord.File(fp, filename=name), **kwargs)

    async def maybe_delete(self, message: Optional[discord.Message] = None):
        if message is not None:
            await message.delete(delay=0)

    async def send(self, content: Any = None, **kwargs: Any) -> Optional[discord.Message]:
        if not (_perms := self.channel.permissions_for(self.me)).send_messages:
            try:
                await self.author.send(
                    "I can't send any messages in that channel. \nPlease give me sufficient permissions to do so."
                )
            except discord.Forbidden:
                pass
            return None

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

    async def wait_and_purge(
        self,
        channel: Union[discord.TextChannel, discord.Thread],
        *,
        limit: int = 100,
        wait_for: Union[int, float] = 10,
        check: Callable = lambda m: True,
    ):
        await asyncio.sleep(wait_for)

        with suppress(discord.HTTPException):
            await channel.purge(limit=limit, check=check)

    async def premium_mango(self, msg: str = "This feature requires Quotient Premium.") -> Optional[discord.Message]:
        from cogs.premium.views import PremiumView

        _view = PremiumView(msg)
        return await self.send(embed=_view.premium_embed, view=_view, embed_perms=True)
