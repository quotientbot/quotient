from models import BaseDbModel
from tortoise import fields
from models.helpers import *

from constants import SSType
from core import Context

from utils import emote
import config

from typing import Tuple
from pydantic import BaseModel, HttpUrl
import imagehash


class ImageResponse(BaseModel):
    url: HttpUrl
    dhash: str
    phash: str
    text: str

    @property
    def lower_text(self):
        return self.text.lower().replace(" ", "").replace("\n", "")


class SSData(BaseDbModel):
    class Meta:
        table = "ss_data"

    id = fields.IntField(pk=True)
    author_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()
    dhash = fields.CharField(max_length=1024, null=True)
    phash = fields.CharField(max_length=1024, null=True)
    submitted_at = fields.DatetimeField(auto_now=True)

    @property
    def author(self):
        return self.bot.get_user(self.author_id)

    @property
    def jump_url(self):
        return "https://discord.com/channels/{}/" + f"{self.channel_id}/{self.message_id}"


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

    def emoji(self, _bool: bool = False):
        return emote.check if _bool else "⚠️"

    def __str__(self):
        _f = self.ss_type.value.title()
        if self.ss_type == SSType.custom:
            _f += f"(`{self.keywords[0]}`)"

        return f"{getattr(self.channel,'mention','deleted-channel')} - {_f}"

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

    @property
    def filtered_keywords(self):
        _l = [self.channel_name.lower().replace(" ", "")]
        for _ in self.keywords:
            _l.append(_.lower().replace(" ", ""))

        return _l

    async def _add_to_data(self, ctx: Context, img: ImageResponse):
        data = await SSData.create(
            author_id=ctx.author.id,
            channel_id=ctx.channel.id,
            message_id=ctx.message.id,
            dhash=img.dhash,
            phash=img.phash,
        )
        await self.data.add(data)

    async def _match_for_duplicate(self, dhash: str, phash: str, author_id: int) -> Tuple[bool, str]:

        _dhash = imagehash.hex_to_hash(dhash)
        async for record in self.data.filter(author_id=author_id).order_by("submitted_at"):
            if _dhash - imagehash.hex_to_hash(record.dhash) <= 7:
                return True, f"{self.emoji(False)} | You've already submitted this screenshot once.\n"

        if r := await self.data.filter(dhash=dhash, phash=phash).first():
            return (
                True,
                f"{self.emoji(False)} | <@{r.author_id}>, already submitted the [same ss]({r.jump_url.format(self.guild_id)}).\n",
            )

        return False, False

    async def verify_yt(self, ctx: Context, image: ImageResponse):
        if not any(_ in image.lower_text for _ in ("subscribe", "videos")):
            return f"{self.emoji()} | This is not a valid youtube ss.\n"

        elif not self.channel_name.lower().replace(" ", "") in image.lower_text:
            return f"{self.emoji()} | Screenshot must belong to [`{self.channel_name}`]({self.channel_link}) channel.\n"

        elif "SUBSCRIBE " in image.text.replace("\n", " "):
            return f"{self.emoji()} | You must subscribe [`{self.channel_name}`]({self.channel_link}) to get verified.\n"

        await self._add_to_data(ctx, image)
        return f"{self.emoji(True)} | Verified successfully.\n"

    async def verify_insta(self, ctx: Context, image: ImageResponse):
        if not "followers" in image.lower_text:
            return f"{self.emoji()} | This is not a valid instagram ss.\n"

        elif not self.channel_name.lower().replace(" ", "") in image.lower_text:
            return f"{self.emoji()} | Screenshot must belong to [`{self.channel_name}`]({self.channel_link}) page.\n"

        elif "FOLLOW " in image.text.replace("\n", " "):
            return f"{self.emoji()} | You must follow [`{self.channel_name}`]({self.channel_link}) to get verified.\n"

        await self._add_to_data(ctx, image)
        return f"{self.emoji(True)} | Verified successfully.\n"

    async def verify_loco(self, ctx: Context, image: ImageResponse):
        if not self.channel_name.lower().replace(" ", "") in image.lower_text:
            return f"{self.emoji()} | Screenshot must belong to [`{self.channel_name}`]({self.channel_link}) channel.\n"

        elif "FOLLOW" in image.text and not "FOLLOWING" in image.text:
            return f"{self.emoji()} | You must follow [`{self.channel_name}`]({self.channel_link}) to get verified.\n"

        await self._add_to_data(ctx, image)
        return f"{self.emoji(True)} | Verified successfully.\n"

    async def verify_rooter(self, ctx: Context, image: ImageResponse):
        if not self.channel_name.lower().replace(" ", "") in image.lower_text:
            return f"{self.emoji()} | Screenshot must belong to [`{self.channel_name}`]({self.channel_link}) channel.\n"

        elif "FOLLOW" in image.text and not "FOLLOWING" in image.text:
            return f"{self.emoji()} | You must follow [`{self.channel_name}`]({self.channel_link}) to get verified.\n"

        await self._add_to_data(ctx, image)
        return f"{self.emoji(True)} | Verified successfully.\n"

    async def verify_custom(self, ctx: Context, image: ImageResponse):

        if not any(_ in image.lower_text for _ in self.filtered_keywords):
            return f"{self.emoji()} | This is not a valid {self.keywords[0]} ss.\n"

        await self._add_to_data(ctx, image)
        return f"{self.emoji(True)} | Verified successfully.\n"
