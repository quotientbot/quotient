from core import Quotient, Cog, Context
from models import Logging
from utils import LogType
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
        self.bot.dispatch("snipe_deleted", message)
        guild = message.guild

        check = await Logging.get_or_none(guild_id=guild.id, type=LogType.msg)
        if check:
            if message.author.bot and check.ignore_bots:
                return
            else:
                self.bot.dispatch("log", LogType.msg, message=message, subtype="single")
