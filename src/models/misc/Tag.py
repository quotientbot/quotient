from tortoise import fields, models


class Tag(models.Model):
    class Meta:
        table = "tags"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=100)
    content = fields.TextField()
    is_embed = fields.BooleanField(default=False)
    is_nsfw = fields.BooleanField(default=False)
    owner_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)
    usage = fields.IntField(default=0)

    @property
    def owner(self):
        return self.bot.get_user(self.owner_id)
