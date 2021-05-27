from discord import permissions
from models import Logging
from typing import Optional
from utils import LogType
import discord


async def audit_entry(guild, action=None):
    records = await guild.audit_logs(limit=1, action=action, oldest_first=False).flatten()
    return records


async def handle_no_channel(_type: LogType, guild: discord.Guild, **kwargs):
    pass


async def handle_no_permission(_type: LogType, channel: discord.TextChannel, **kwargs):
    pass


async def check_permissions(_type, guild: discord.Guild, channel: discord.TextChannel) -> bool:
    if not guild.me.guild_permissions.view_audit_log:
        return await handle_no_permission(_type, channel, permissions=("", ""))

    elif not channel.permissions_for(guild.me).send_messages or not channel.permissions_for(guild.me).embed_links:
        return await handle_no_permission(_type, channel, permissions=("", ""))


async def get_channel(_type: LogType, guild: discord.Guild) -> Optional[discord.TextChannel]:
    check = await Logging.filter(type=_type, guild_id=guild.id).first()
    if not check:
        return None

    channel = check.channel
    color = check.color
    if not channel:
        return await handle_no_channel(_type, guild)

    else:
        return channel, color
