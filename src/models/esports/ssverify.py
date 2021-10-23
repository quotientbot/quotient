from models import BaseDbModel
from tortoise import fields, models
from models.helpers import *

from constants import SSType, SSStatus


class SSVerify(BaseDbModel):
    class Meta:
        table = "ss_info"

    id = fields.IntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    msg_channel_id = fields.BigIntField(index=True)
    log_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_ss = fields.IntField()
    channel_name = fields.CharField(max_length=50)
    channel_link = fields.CharField(max_length=150)
    logo_link = fields.CharField(max_length=150)
    ss_type = fields.CharEnumField(SSType)
    success_message = fields.CharField(null=True, max_lenght=400)
    delete_after = fields.IntField(default=0)
    sstoggle = fields.BooleanField(default=True)
    data: fields.ManyToManyRelation["SSData"] = fields.ManyToManyField("models.SSData", index=True)

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)


class SSData(BaseDbModel):
    class Meta:
        table = "ss_data"

    id = fields.BigIntField(pk=True)
    author_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    hash = fields.CharField(max_length=50, null=True)
    submitted_at = fields.DatetimeField(auto_now=True)
