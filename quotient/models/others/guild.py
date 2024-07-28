import os

import discord
from tortoise import fields

from quotient.models import BaseDbModel


class Guild(BaseDbModel):
    class Meta:
        table = "guilds"

    guild_id = fields.BigIntField(primary_key=True, db_index=True, generated=False)
    prefix = fields.CharField(default=os.getenv("DEFAULT_PREFIX"), max_length=5)

    is_premium = fields.BooleanField(default=False)
    made_premium_by = fields.BigIntField(null=True)
    premium_end_time = fields.DatetimeField(null=True)

    @property
    def _guild(self) -> discord.Guild:
        return self.bot.get_guild(self.guild_id)
