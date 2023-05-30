from tortoise import fields, models


class Snipe(models.Model):
    class Meta:
        table = "snipes"

    channel_id = fields.BigIntField(pk=True)
    author_id = fields.BigIntField()
    content = fields.TextField()
    delete_time = fields.DatetimeField(auto_now=True)
    nsfw = fields.BooleanField(default=False)

    @property
    def author(self):
        return self.bot.get_user(self.author_id)
