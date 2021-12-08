from __future__ import annotations
import typing


if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog, right_bot_check
from models import Timer, Lockdown
from constants import LockType


class LockEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    @right_bot_check()
    async def on_lockdown_timer_complete(self, timer: Timer):
        _type = timer.kwargs["_type"]

        if _type == LockType.channel.value:
            channel_id = timer.kwargs["channel_id"]

            check = await Lockdown.get_or_none(channel_id=channel_id, type=LockType.channel)
            if not check or check.expire_time != timer.expires:
                return

            channel = self.bot.get_channel(channel_id)
            if not channel or not channel.permissions_for(channel.guild.me).manage_channels:
                return

            perms = channel.overwrites_for(channel.guild.default_role)
            perms.send_messages = True
            await channel.set_permissions(channel.guild.default_role, overwrite=perms, reason="Lockdown timer complete!")
            await Lockdown.filter(channel_id=channel.id).delete()
            await channel.send(f"Unlocked **{channel}**")

        elif _type == LockType.guild.value:

            guild_id = timer.kwargs["guild_id"]

            check = await Lockdown.get_or_none(guild_id=guild_id, type=LockType.guild)
            if not check or check.expire_time != timer.expires:
                return

            for channel in check.channels:
                if channel is not None and channel.permissions_for(channel.guild.me).manage_channels:

                    perms = channel.overwrites_for(channel.guild.default_role)
                    perms.send_messages = True
                    await channel.set_permissions(
                        channel.guild.default_role, overwrite=perms, reason="Lockdown timer complete!"
                    )
            await Lockdown.filter(guild_id=guild_id, type=LockType.guild).delete()
            channel = self.bot.get_channel(check.channel_id)
            if channel is not None and channel.permissions_for(channel.guild.me).send_messages:
                await channel.send(f"Unlocked **server**.")
