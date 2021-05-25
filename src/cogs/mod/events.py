from core import Cog, Quotient, Context
from models import Timer, Lockdown
from utils import LockType
import discord

__all__ = ("ModEvents",)


class ModEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Mute them if they were muted
        """
        pass

    @Cog.listener()
    async def on_lockdown_timer_complete(self, timer: Timer):
        _type = timer.kwargs["_type"]

        if _type == LockType.channel.value:
            channel_id = timer.kwargs["channel_id"]

            channel = self.bot.get_channel(channel_id)
            if not channel or not channel.permissions_for(channel.guild.me).manage_channels:
                return

            perms = channel.overwrites_for(channel.guild.default_role)
            perms.send_messages = True
            await channel.set_permissions(channel.guild.default_role, overwrite=perms, reason="Lockdown timer complete!")
