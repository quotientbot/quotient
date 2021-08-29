from tortoise import fields, models
from models.helpers import *

import discord
from async_property import async_property


class SlotManager(models.Model):
    class Meta:
        table = "slot_manager"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    main_channel_id = fields.BigIntField()
    updates_channel_id = fields.BigIntField()

    message_id = fields.BigIntField()

    toggle = fields.BooleanField(default=True)
    locks: fields.ManyToManyRelation["SlotLocks"] = fields.ManyToManyField("models.SlotLocks", index=True)

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def main_channel(self):
        return self.bot.get_channel(self.main_channel_id)

    @property
    def updates_channel(self):
        return self.bot.get_channel(self.updates_channel_id)

    @async_property
    async def message(self):
        channel = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, self.main_channel_id)
        if channel:
            return await channel.fetch_message(self.message_id)

    @property
    def logschan(self):
        if g := self.guild is not None:
            return discord.utils.get(g.text_channels, name="quotient-scrims-logs")


class SlotLocks(models.Model):
    class Meta:
        table = "slot_locks"

    id = fields.IntField(pk=True)
    lock_at = fields.DatetimeField(null=True)
    locked = fields.BooleanField(default=True)
