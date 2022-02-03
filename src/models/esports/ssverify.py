from models import BaseDbModel
from tortoise import fields, exceptions
from models.helpers import *

from constants import SSType
import imagehash

from utils import emote
import config

from discord.ext.commands import TextChannelConverter, BadArgument


class SSData(BaseDbModel):
    class Meta:
        table = "ss_data"

    id = fields.IntField(pk=True)
    author_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    hash = fields.CharField(max_length=50, null=True)
    submitted_at = fields.DatetimeField(auto_now=True)

    @property
    def author(self):
        return self.bot.get_user(self.author_id)


class SSVerify(BaseDbModel):
    class Meta:
        table = "ss_info"

    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField(index=True)
    guild_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_ss = fields.IntField(default=4)
    channel_name = fields.CharField(max_length=50)
    channel_link = fields.CharField(max_length=150, default=config.SERVER_LINK)

    keywords = ArrayField(fields.CharField(max_length=50), default=list)
    allow_same = fields.BooleanField(default=False)

    ss_type = fields.CharEnumField(SSType)

    success_message = fields.CharField(null=True, max_length=500)

    data: fields.ManyToManyRelation["SSData"] = fields.ManyToManyField("models.SSData", index=True)

    @classmethod
    async def convert(cls, ctx, argument: str):
        try:
            channel = await TextChannelConverter().convert(ctx, argument)
        except:
            pass

        else:
            try:
                return await cls.get(channel_id=channel.id)
            except exceptions.DoesNotExist:
                pass

        raise BadArgument(f"Kindly mention a valid ssverification channel or use `{ctx.prefix}ssverify list`")

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    @property
    def role(self):
        if g := self._guild:
            return g.get_role(self.role_id)

    def emoji(self, _bool):
        return emote.check if _bool else "⚠️"

    def __str__(self):
        return f"{getattr(self.channel,'mention','deleted-channel')} - {self.ss_type.name.title()}"

    async def all_hashes(self, _bool=False):
        async for _ in self.data.all():
            yield hash if not _bool else imagehash.hex_to_hash(_)

    async def find_hash(self, hash: str):
        return await self.data.filter(hash=hash).first()

    async def find_similar_hash(self, hash: str, distance: int = 10):
        a_hash = imagehash.hex_to_hash(hash)
        async for _ in self.all_hashes(True):
            if a_hash - _ in range(distance + 1):
                return await SSData.get(hash=str(_))

    async def is_user_verified(self, user_id: int):
        return await self.data.filter(author_id=user_id).count() >= self.required_ss

    async def required_by_user(self, user_id: int):
        diff = self.required_ss - await self.data.filter(author_id=user_id).count()
        return 0 if diff <= 0 else diff

    async def full_delete(self):

        self.bot.cache.ssverify_channels.discard(self.channel_id)
        data = await self.data.all()

        await SSData.filter(pk__in=[d.id for d in data]).delete()
        await self.delete()
