from tortoise import fields

from quotient.models import BaseDbModel


class Command(BaseDbModel):
    class Meta:
        table = "commands"

    id = fields.IntField(primary_key=True)
    guild_id = fields.BigIntField(db_index=True)
    channel_id = fields.BigIntField()
    author_id = fields.BigIntField(db_index=True)
    used_at = fields.DatetimeField(auto_now_add=True)
    prefix = fields.CharField(max_length=50)
    name = fields.CharField(max_length=100)
    failed = fields.BooleanField(default=False)
    app_command = fields.BooleanField(default=False)
