import constants
from models.helpers import ArrayField
from tortoise import fields, models


class Lockdown(models.Model):
    class Meta:
        table = "lockdown"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    type = fields.CharEnumField(constants.LockType, max_length=20)
    role_id = fields.BigIntField(null=True)
    channel_id = fields.BigIntField(null=True)
    channel_ids = ArrayField(fields.BigIntField(), default=list, index=True)
    expire_time = fields.DatetimeField(null=True)
    author_id = fields.BigIntField()

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def roles(self):
        if self._guild is not None:
            return self._guild.get_role(self.role_id)

    @property
    def channels(self):
        return map(self.bot.get_channel, self.channel_ids)
