from tortoise import fields

from quotient.models import BaseDbModel


class AutoPurge(BaseDbModel):
    class Meta:
        table = "autopurge"

    id = fields.IntField(primary_key=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    delete_after = fields.IntField(default=10)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)
