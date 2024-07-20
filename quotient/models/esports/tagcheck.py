import discord
from models import BaseDbModel
from tortoise import fields


class TagCheck(BaseDbModel):
    class Meta:
        table = "tagcheck"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    required_mentions = fields.IntField(default=0)

    @property
    def _guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)

    @property
    def channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.channel_id)

    @property
    def ignorerole_role(self) -> discord.Role:
        if not self._guild is None:
            return discord.utils.get(self._guild.roles, name="quotient-tag-ignore")

    def __str__(self):
        return f"{getattr(self.channel,'mention','#unknown-channel')} (Mentions: `{self.required_mentions}`)"
