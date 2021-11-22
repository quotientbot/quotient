from tortoise import models, fields
from models.helpers import *
import config
import discord

_dict = {"view": None, "embed": None, "scrims": None, "idp": None, "ptable": None, "tourney": None, "slotm": None}


class Guild(models.Model):
    class Meta:
        table = "guild_data"

    guild_id = fields.BigIntField(pk=True, index=True)
    bot_id = fields.BigIntField(default=config.MAIN_BOT)
    waiting_activation = fields.BooleanField(default=False)

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
