from models import BaseDbModel

from tortoise import fields
from models.helpers import ArrayField
from .scrims import Scrim

from typing import List
import discord

from contextlib import suppress


class ScrimsSlotManager(BaseDbModel):
    class Meta:
        table = "scrims_slotmanager"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    main_channel_id = fields.BigIntField()
    updates_channel_id = fields.BigIntField()

    message_id = fields.BigIntField()

    toggle = fields.BooleanField(default=True)
    allow_reminders = fields.BooleanField(default=True)

    scrim_ids = ArrayField(fields.BigIntField(), default=list)

    @classmethod
    async def convert(self, ctx, argument: str) -> "ScrimsSlotManager":
        ...

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    async def scrims(self) -> List[Scrim]:
        return await Scrim.filter(pk__in=self.scrim_ids)

    @property
    def main_channel(self):
        return self.bot.get_channel(self.main_channel_id)

    @property
    def updates_channel(self):
        return self.bot.get_channel(self.updates_channel_id)

    @property
    def logschan(self):
        if (g := self.guild) is not None:
            return discord.utils.get(g.text_channels, name="quotient-scrims-logs")

    async def message(self):
        channel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, self.main_channel_id)
        if channel:
            _m = None
            with suppress(discord.HTTPException):
                _m = await channel.fetch_message(self.message_id)

            return _m
