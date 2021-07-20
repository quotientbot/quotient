from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .base import IpcCog
from discord.ext import ipc
from models import Guild


class SettingsIpc(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @ipc.server.route()
    async def get_member_count(self, data):
        guild = self.bot.get_guild(data.guild_id)
        return guild.member_count

    @ipc.server.route()
    async def update_guild_settings(self, payload):
        guild_id = payload.guild_id

        guild = await Guild.get(guild_id=int(guild_id))

        self.bot.guild_data[guild.guild_id] = {
            "prefix": guild.prefix,
            "color": guild.embed_color,
            "footer": guild.embed_footer,
        }
        return self.positive
