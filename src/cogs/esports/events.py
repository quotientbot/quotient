from core import Quotient, Cog, Context
from models import EasyTag
from contextlib import suppress
import discord
import re


class ScrimEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_eztag_msg(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if not message.channel.id in self.bot.eztagchannels:
            return

        channel_id = message.channel.id

        eztag = await EasyTag.get_or_none(channel_id=channel_id)

        if not eztag:
            return

        ignore_role = eztag.ignorerole

        if ignore_role != None and ignore_role in message.author.roles:
            return

        with suppress(discord.Forbidden, discord.NotFound):

            tags = set(re.findall(r"\b\d{18}\b|\b@\w+", message.content, re.IGNORECASE))
