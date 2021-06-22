from core import Quotient, Cog, Context
from models import Logging
from constants import LogType
from contextlib import suppress
import discord

__all__ = ("LoggingDispatchers",)


class LoggingDispatchers(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    # ====================================================================================
    # ==================================================================================== MESSAGE (DELETE, BULK DELETE, EDIT) EVENTS
    # ====================================================================================

    @Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # not using raw_message_delete because if cached_message is None , there is nothing to log.
        self.bot.dispatch("snipe_deleted", message)
        guild = message.guild

        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.msg)
        if check:
            if message.author.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.msg, message=message, subtype="single")

    @Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages[0].guild:
            return

        guild = messages[0].guild
        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.msg)
        if check:
            if messages[0].author.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.msg, message=messages, subtype="bulk")

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild:
            return

        with suppress(AttributeError):
            if before.content == after.content:
                return

        check = await Logging.get_or_none(guild_id=before.guild.id, type=LogType.msg)
        if check:
            if before.author.bot and check.ignore_bots:
                return

            else:
                self.bot.dispatch("log", LogType.msg, message=(before, after))
