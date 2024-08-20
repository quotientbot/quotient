import discord
import imagehash
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

    def __str__(self):
        return f"{getattr(self.channel,'mention','`unknown-channel`')} (`{self.screenshot_type.value}`)"

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def success_role(self) -> discord.Role | None:
        return self._guild.get_role(self.role_id)

    @property
    def channel(self) -> discord.TextChannel | None:
        return self._guild.get_channel(self.channel_id)

    @property
    def default_entity_link(self) -> str:
        return self.entity_link or self.bot.config("SUPPORT_SERVER_LINK")

    async def full_delete(self):
        self.bot.cache.ssverify_channel_ids.discard(self.channel_id)

        await SSverifyEntry.filter(ssverify=self).delete()
        await self.delete()

    async def check_duplicate_ss(self, dHash: str, author_id: int):
        from quotient.lib.emojis import CROSS

        resolved_dHash = imagehash.hex_to_hash(dHash[2:])
        user_entries = [entry for entry in self.entries if entry.author_id == author_id]

        if duplicate_records := [entry for entry in self.entries if dHash == entry.dHash]:
            return (
                True,
                f"{CROSS} | You've already submitted this screenshot [here]({duplicate_records[0].jump_url(self.guild_id)}).\n",
            )

        if duplicate_records := [entry for entry in user_entries if resolved_dHash - imagehash.hex_to_hash(entry.dHash) <= 7]:
            return True, f"{CROSS} | You've already submitted this screenshot [here]({duplicate_records[0].jump_url(self.guild_id)})\n"

        return False, False


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

    def jump_url(self, guild_id: int) -> str:
        return f"https://discord.com/channels/{guild_id}/{self.channel_id}/{self.message_id}"
