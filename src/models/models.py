from typing import Optional

import constants
import discord
from tortoise import fields, models

from .helpers import *

__all__ = (
    "User",
    "Tag",
    "Timer",
    "Snipe",
    "Autorole",
    "Votes",
    "Premium",
    "Lockdown",
    "Commands",
    "AutoPurge",
)

# ************************************************************************************************


# TODO: make manytomany field in user_data for redeem codes.
class User(models.Model):
    class Meta:
        table = "user_data"

    user_id = fields.BigIntField(pk=True, index=True)
    is_premium = fields.BooleanField(default=False, index=True)
    premium_expire_time = fields.DatetimeField(null=True)
    made_premium = ArrayField(fields.BigIntField(), default=list)  # a list of servers this user boosted
    premiums = fields.IntField(default=0)
    premium_notified = fields.BooleanField(default=False)
    public_profile = fields.BooleanField(default=True)
    # badges = CharVarArrayField(default=list)
    money = fields.IntField(default=0)


# ************************************************************************************************


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


# ************************************************************************************************

# ************************************************************************************************
class Timer(models.Model):
    id = fields.BigIntField(pk=True)
    expires = fields.DatetimeField(index=True)
    created = fields.DatetimeField(auto_now=True)
    event = fields.TextField()
    extra = fields.JSONField(default=dict)

    @property
    def kwargs(self):
        return self.extra.get("kwargs", {})

    @property
    def args(self):
        return self.extra.get("args", ())


# ************************************************************************************************
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


# ************************************************************************************************
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


# ************************************************************************************************


class Votes(models.Model):
    class Meta:
        table = "votes"

    user_id = fields.BigIntField(pk=True)
    is_voter = fields.BooleanField(default=False, index=True)
    expire_time = fields.DatetimeField(null=True)
    reminder = fields.BooleanField(default=False)
    notified = fields.BooleanField(default=False, index=True)
    public_profile = fields.BooleanField(default=True)
    total_votes = fields.IntField(default=0)


# ************************************************************************************************


class Premium(models.Model):
    class Meta:
        table = "premium_logs"

    order_id = fields.CharField(max_length=50, pk=True)
    user_id = fields.BigIntField()
    payment_id = fields.CharField(max_length=50, null=True)
    payment_time = fields.DatetimeField(null=True)
    plan_type = fields.IntField(default=0, null=True)
    plan_2 = fields.IntField(default=0, null=True)
    plan_3 = fields.IntField(default=0, null=True)
    amount = fields.IntField(default=0, null=True)
    token = fields.TextField(null=True)
    is_done = fields.BooleanField(default=False, null=True)
    order_time = fields.DatetimeField(null=True)
    username = fields.CharField(max_length=200, null=True)
    email = fields.CharField(max_length=200, null=True)
    is_notified = fields.BooleanField(default=False, null=True)


# ************************************************************************************************


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


# ************************************************************************************************


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
