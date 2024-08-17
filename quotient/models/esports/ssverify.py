import discord
from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField

from quotient.models import BaseDbModel

from .enums import ScreenshotType


class SSverify(BaseDbModel):
    class Meta:
        table = "ssverification"

    id = fields.IntField(primary_key=True)
    channel_id = fields.BigIntField()
    guild_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_ss = fields.SmallIntField(default=4)

    entity_name = fields.CharField(max_length=50)
    entity_link = fields.CharField(max_length=200, null=True)

    possible_keywords = ArrayField("VARCHAR(50)", default=list)  # only used if screenshot_type is custom
    allow_duplicate_ss = fields.BooleanField(default=False)

    success_message = fields.CharField(max_length=500, null=True)
    screenshot_type = fields.CharEnumField(ScreenshotType)

    entries: fields.ReverseRelation["SSverifyEntry"]


class SSverifyEntry(BaseDbModel):
    class Meta:
        table = "ssverification_entries"

    id = fields.IntField(pk=True)
    author_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    dHash = fields.CharField(max_length=1024, null=True)
    submitted_at = fields.DatetimeField(auto_now_add=True)

    ssverify: fields.ForeignKeyRelation[SSverify] = fields.ForeignKeyField("default.SSverify", related_name="entries")

    @property
    def author(self) -> discord.User | None:
        return self.bot.get_user(self.author_id)

    @property
    def jump_url(self) -> str:
        return f"https://discord.com/channels/{self.channel_id}/{self.message_id}"
