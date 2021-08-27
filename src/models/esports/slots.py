from tortoise import fields, models
from models.helpers import *

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


class SlotLocks(models.Model):
    class Meta:
        table = "slot_locks"

    id = fields.BigIntField(pk=True)
    autolock = fields.BooleanField(default=True)
    lock_at = fields.DatetimeField(auto_now=True)
    locked = fields.BooleanField(default=True)
