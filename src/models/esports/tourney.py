from contextlib import suppress
from tortoise import fields, exceptions
from discord.ext.commands import BadArgument

from typing import Optional, List, Union
from models.helpers import *

from models import BaseDbModel

from utils import split_list

import discord

_dict = {
    "tick": "✅",
    "cross": "❌",
}

from core import Context


class Tourney(BaseDbModel):
    class Meta:
        table = "tm.tourney"

    id = fields.BigIntField(pk=True, index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=30, default="Quotient-Tourney")
    registration_channel_id = fields.BigIntField(index=True)
    confirm_channel_id = fields.BigIntField()
    role_id = fields.BigIntField()
    required_mentions = fields.SmallIntField(validators=[ValueRangeValidator(range(0, 11))])
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

    success_message = fields.CharField(max_length=500, null=True)

    emojis = fields.JSONField(default=_dict)

    slotm_channel_id = fields.BigIntField(null=True)
    slotm_message_id = fields.BigIntField(null=True)

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
        return self.emojis.get("tick", "✅")

    @property
    def cross_emoji(self):
        return self.emojis.get("cross", "❌")

    @staticmethod
    def is_ignorable(member: discord.Member) -> bool:
        return "tourney-mod" in (role.name for role in member.roles)

    async def get_groups(self, size: int) -> List[List["TMSlot"]]:
        return split_list(await self.assigned_slots.all().order_by("num"), size)

    async def get_group(self, num: int, size: int) -> Union[List["TMSlot"], None]:
        _list = await self.get_groups(size)
        for _chunk in _list:
            if _list.index(_chunk) == num - 1:
                return _chunk

    async def add_assigned_slot(self, slot: "TMSlot", message: discord.Message):
        _e = discord.Embed(color=0x00FFB3)
        _e.description = f"**{slot.num}) NAME: [{slot.team_name.upper()}]({slot.jump_url})**\n"

        if len(message.mentions) > 0:
            _e.description += f"Team: {', '.join([str(m) for m in message.mentions])}"

        if _chan := self.confirm_channel:
            m = await _chan.send(
                content=message.author.mention, embed=_e, allowed_mentions=discord.AllowedMentions(users=True)
            )

            slot.confirm_jump_url = m.jump_url

            await slot.save()
            await self.assigned_slots.add(slot)

    async def finalize_slot(self, ctx: Context):
        """
        Add role to user and reaction to the message
        """
        with suppress(discord.HTTPException):
            await ctx.author.add_roles(self.role)
            await ctx.message.add_reaction(self.check_emoji)

            if self.success_message:
                embed = ctx.bot.embed(ctx, title="Tournament Registration Successful", description=self.success_message)
                await ctx.author.send(embed=embed)


class TMSlot(BaseDbModel):
    class Meta:
        table = "tm.register"

    id = fields.BigIntField(pk=True)
    num = fields.IntField()
    team_name = fields.TextField()
    leader_id = fields.BigIntField()
    members = ArrayField(fields.BigIntField(), default=list)
    confirm_jump_url = fields.CharField(max_length=300, null=True)
    jump_url = fields.TextField(null=True)


class MediaPartner(BaseDbModel):
    class Meta:
        table = "tm.media_partners"

    channel_id = fields.BigIntField(pk=True, generated=False)
    tourney_id = fields.IntField()
    role_id = fields.BigIntField(null=True)
    mentions = fields.SmallIntField(validators=[ValueRangeValidator(range(1, 11))])
    slots: fields.ManyToManyRelation["PartnerSlot"] = fields.ManyToManyField("models.PartnerSlot")

    @property
    def channel(self) -> Optional[discord.TextChannel]:
        return self.bot.get_channel(self.channel_id)


class PartnerSlot(BaseDbModel):
    class Meta:
        table = "tm.media_partner_users"

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    jump_url = fields.CharField(max_length=300, null=True)
    members = ArrayField(fields.BigIntField(), default=list)
