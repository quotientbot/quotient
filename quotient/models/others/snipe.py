from models import BaseDbModel
from tortoise import fields


class Snipe(BaseDbModel):
    class Meta:
        table = "snipes"

    channel_id = fields.BigIntField(primary_key=True)
    author_id = fields.BigIntField()

    content = fields.CharField(max_length=2000)

    deleted_at = fields.DatetimeField(auto_now=True)
    nsfw = fields.BooleanField(default=False)

    @property
    def author(self):
        return self.bot.get_user(self.author_id)
