from typing import Optional
import constants
import discord
from models.helpers import ArrayField
from tortoise import fields, models

import config
from models import BaseDbModel
from models.helpers import *

_dict = {"embed": [], "scrims": [], "tourney": [], "slotm": []}


class Guild(BaseDbModel):
    class Meta:
        table = "guild_data"

    guild_id = fields.BigIntField(pk=True, index=True)

    prefix = fields.CharField(default="q", max_length=5)
    embed_color = fields.IntField(default=65459, null=True)
    embed_footer = fields.TextField(default=config.FOOTER)

    tag_enabled_for_everyone = fields.BooleanField(default=True)  # ye naam maine ni rkha sachi

    is_premium = fields.BooleanField(default=False)
    made_premium_by = fields.BigIntField(null=True)
    premium_end_time = fields.DatetimeField(null=True)
    premium_notified = fields.BooleanField(default=False)

    public_profile = fields.BooleanField(default=True)  # whether to list the server on global leaderboards

    private_channel = fields.BigIntField(null=True)

    dashboard_access = fields.JSONField(default=_dict)

    @property
    def _guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)

    @property
    def private_ch(self) -> discord.TextChannel:
        if (g := self._guild) is not None:
            return g.get_channel(self.private_channel)

    @property
    def booster(self):
        return self.bot.get_user(self.made_premium_by)


class Autorole(models.Model):
    class Meta:
        table = "autoroles"

    guild_id = fields.BigIntField(pk=True, index=True)
    humans = ArrayField(fields.BigIntField(), default=list)
    bots = ArrayField(fields.BigIntField(), default=list)

    @property
    def _guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def human_roles(self):
        if self._guild is not None:
            return tuple(map(lambda x: getattr(self._guild.get_role(x), "mention", "Deleted"), self.humans))

    @property
    def bot_roles(self):
        if self._guild is not None:
            return tuple(map(lambda x: getattr(self._guild.get_role(x), "mention", "Deleted"), self.bots))


class Lockdown(models.Model):
    class Meta:
        table = "lockdown"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    type = fields.CharEnumField(constants.LockType, max_length=20)
    role_id = fields.BigIntField(null=True)
    channel_id = fields.BigIntField(null=True)
    channel_ids = ArrayField(fields.BigIntField(), default=list, index=True)
    expire_time = fields.DatetimeField(null=True)
    author_id = fields.BigIntField()

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def roles(self):
        if self._guild is not None:
            return self._guild.get_role(self.role_id)

    @property
    def channels(self):
        return map(self.bot.get_channel, self.channel_ids)


class Commands(models.Model):
    class Meta:
        table = "commands"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField()
    user_id = fields.BigIntField(index=True)
    cmd = fields.CharField(max_length=100, index=True)
    used_at = fields.DatetimeField(auto_now=True)
    prefix = fields.CharField(max_length=100)
    failed = fields.BooleanField(default=False)


class AutoPurge(models.Model):
    class Meta:
        table = "autopurge"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    delete_after = fields.IntField(default=10)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)


