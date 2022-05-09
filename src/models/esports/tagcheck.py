from typing import Optional

import discord
from tortoise import fields, models

from models import BaseDbModel
from models.helpers import *


class TagCheck(BaseDbModel):
    class Meta:
        table = "tagcheck"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    required_mentions = fields.IntField(default=0)
    delete_after = fields.BooleanField(default=False)

    @property
    def _guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)

    @property
    def ignorerole(self) -> Optional[discord.Role]:
        if not self._guild is None:
            return discord.utils.get(self._guild.roles, name="quotient-tag-ignore")

    def __str__(self):
        return f"{getattr(self.channel,'mention','channel-not-found')} (Mentions: `{self.required_mentions}`)"


class EasyTag(BaseDbModel):
    class Meta:
        table = "easytags"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField(index=True)
    delete_after = fields.BooleanField(default=False)

    @property
    def _guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)

    @property
    def ignorerole(self) -> Optional[discord.Role]:
        if not self._guild is None:
            return discord.utils.get(self._guild.roles, name="quotient-tag-ignore")
