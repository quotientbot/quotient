from typing import Optional

import discord
from tortoise import fields, models

from models.helpers import ArrayField


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
