from tortoise import models, fields, exceptions, validators
from discord.ext.commands import BadArgument

from typing import Optional
from models.helpers import *

import discord

_dict = {
    "tick": "✅",
    "cross": "❌",
}


class Tourney(models.Model):
    class Meta:
        table = "tm.tourney"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=30, default="Quotient-Tourney")
    registration_channel_id = fields.BigIntField(index=True)
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.SmallIntField(validators=[ValueRangeValidator(range(1, 11))])
    total_slots = fields.SmallIntField(validators=[ValueRangeValidator(range(1, 10001))])
    banned_users = ArrayField(fields.BigIntField(), default=list)
    host_id = fields.BigIntField()
    multiregister = fields.BooleanField(default=False)
    started_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    open_role_id = fields.BigIntField(null=True)
    teamname_compulsion = fields.BooleanField(default=False)

    ping_role_id = fields.BigIntField(null=True)
    no_duplicate_name = fields.BooleanField(default=True)
    autodelete_rejected = fields.BooleanField(default=False)

    success_message = fields.CharField(max_length=350, null=True)

    emojis = fields.JSONField(default=_dict)

    assigned_slots: fields.ManyToManyRelation["TMSlot"] = fields.ManyToManyField("models.TMSlot")
    media_partners: fields.ManyToManyRelation["MediaPartner"] = fields.ManyToManyField("models.MediaPartner")

    def __str__(self):
        return f"{getattr(self.registration_channel,'mention','deleted-channel')} (Tourney: {self.id})"

    @classmethod
    async def convert(cls, ctx, argument: str):
        try:
            argument = int(argument)
        except ValueError:
            pass
        else:
            try:
                return await cls.get(pk=argument, guild_id=ctx.guild.id)
            except exceptions.DoesNotExist:
                pass

        raise BadArgument(f"This is not a valid Tourney ID.\n\nGet a valid ID with `{ctx.prefix}tourney config`")

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def logschan(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return discord.utils.get(g.text_channels, name="quotient-tourney-logs")

    @property
    def registration_channel(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return g.get_channel(self.registration_channel_id)

    @property
    def confirm_channel(self) -> Optional[discord.TextChannel]:
        if (g := self.guild) is not None:
            return g.get_channel(self.confirm_channel_id)

    @property
    def closed(self):
        return bool(self.closed_at)

    @property
    def role(self) -> Optional[discord.Role]:
        if (g := self.guild) is not None:
            return g.get_role(self.role_id)

    @property
    def open_role(self):
        if (g := self.guild) is not None:
            if self.open_role_id is not None:
                return g.get_role(self.open_role_id)
            return self.guild.default_role

    @property
    def ping_role(self):
        if (g := self.guild) is not None:
            if self.ping_role_id is not None:
                return g.get_role(self.ping_role_id)
            return None

    @property
    def modrole(self):
        if (g := self.guild) is not None:
            return discord.utils.get(g.roles, name="tourney-mod")

    @property
    def check_emoji(self):
        return self.emojis["tick"]

    @property
    def cross_emoji(self):
        return self.emojis["cross"]


class TMSlot(models.Model):
    class Meta:
        table = "tm.register"

    id = fields.BigIntField(pk=True)
    num = fields.IntField()
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    members = ArrayField(fields.BigIntField(), default=list)
    jump_url = fields.TextField(null=True)


class MediaPartner(models.Model):
    class Meta:
        table = "tm.media_partners"

    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField()
    role_id = fields.BigIntField(null=True)
    mentions = fields.SmallIntField(validators=[ValueRangeValidator(range(1, 11))])
    player_ids = ArrayField(fields.BigIntField(), default=list)

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)
