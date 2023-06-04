from tortoise import fields, models


class Commands(models.Model):
    class Meta:
        table = "commands"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField()
    user_id = fields.BigIntField(index=True)
    cmd = fields.CharField(max_length=100, index=True)
    used_at = fields.DatetimeField(auto_now=True)
    prefix = fields.CharField(max_length=100)
    failed = fields.BooleanField(default=False)
