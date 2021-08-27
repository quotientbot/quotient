from tortoise import models, fields, exceptions
from discord.ext.commands import BadArgument

from models.helpers import *

import discord


class Tourney(models.Model):
    class Meta:
        table = "tm.tourney"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=200, default="Quotient-Tourney")
    registration_channel_id = fields.BigIntField(index=True)
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    banned_users = ArrayField(fields.BigIntField(), default=list)
    host_id = fields.BigIntField()
    multiregister = fields.BooleanField(default=False)
    started_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    open_role_id = fields.BigIntField(null=True)
    teamname_compulsion = fields.BooleanField(default=False)

    assigned_slots: fields.ManyToManyRelation["TMSlot"] = fields.ManyToManyField("models.TMSlot")

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
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def logschan(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, name="quotient-tourney-logs")

    @property
    def registration_channel(self):
        if self.guild is not None:
            return self.guild.get_channel(self.registration_channel_id)

    @property
    def confirm_channel(self):
        if self.guild is not None:
            return self.guild.get_channel(self.confirm_channel_id)

    @property
    def closed(self):
        return bool(self.closed_at)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def open_role(self):
        if self.guild is not None:
            if self.open_role_id is not None:
                return self.guild.get_role(self.open_role_id)
            return self.guild.default_role

    @property
    def modrole(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.roles, name="tourney-mod")


class TMSlot(models.Model):
    class Meta:
        table = "tm.register"

    id = fields.BigIntField(pk=True)
    num = fields.IntField()
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    members = ArrayField(fields.BigIntField(), default=list)
    jump_url = fields.TextField(null=True)
