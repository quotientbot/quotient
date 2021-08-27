from tortoise import fields, models
from typing import Optional
from models.helpers import *

import discord


class TagCheck(models.Model):
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


class EasyTag(models.Model):
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
