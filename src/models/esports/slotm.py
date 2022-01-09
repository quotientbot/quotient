from models import BaseDbModel

from tortoise import fields
from models.helpers import ArrayField
from .scrims import Scrim

from typing import List
import discord

from contextlib import suppress
from utils import plural

__all__ = ("ScrimsSlotManager",)


class ScrimsSlotManager(BaseDbModel):
    class Meta:
        table = "scrims_slotmanager"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()
    main_channel_id = fields.BigIntField()

    message_id = fields.BigIntField()

    toggle = fields.BooleanField(default=True)
    allow_reminders = fields.BooleanField(default=True)
    multiple_slots = fields.BooleanField(default=False)

    scrim_ids = ArrayField(fields.BigIntField(), default=list)

    def __str__(self):
        return f"{getattr(self.main_channel,'mention','not-found')} - ({plural(self.scrim_ids):scrim|scrims})"

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

    @staticmethod
    async def from_guild(guild: discord.Guild):
        return await ScrimsSlotManager.filter(guild_id=guild.id)

    @staticmethod
    async def unavailable_scrims(guild: discord.Guild) -> List[int]:
        return [scrim for record in await ScrimsSlotManager.filter(guild_id=guild.id) for scrim in record.scrim_ids]

    @staticmethod
    async def available_scrims(guild: discord.Guild) -> List[Scrim]:
        return await Scrim.filter(pk__not_in=await ScrimsSlotManager.unavailable_scrims(guild))

    async def full_delete(self):
        ...


class SlotReminder(BaseDbModel):
    class Meta:
        table = "scrims_slot_reminders"

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)
