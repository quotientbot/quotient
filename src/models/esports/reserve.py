from tortoise import models, fields


class Subscriptions(models.Model):
    class Meta:
        table = "subscriptions"

    guild_id = fields.BigIntField(pk=True)
    log_channel_id = fields.BigIntField()
