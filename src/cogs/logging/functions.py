from models import Logging
from typing import Optional
from constants import LogType
import discord


async def audit_entry(guild, action=None):
    records = await guild.audit_logs(limit=1, action=action, oldest_first=False).flatten()
    return records


async def handle_no_channel(_type: LogType, guild: discord.Guild, **kwargs):
    pass


async def handle_no_permission(_type: LogType, channel: discord.TextChannel, **kwargs):
    pass


async def check_permissions(_type, channel: discord.TextChannel) -> bool:
    _bool = True

    perms = channel.permissions_for(channel.guild.me)
    if not all((perms.send_messages, perms.embed_links)):
        _bool = False
        await handle_no_permission(_type, channel)

    return _bool


async def get_channel(_type: LogType, guild) -> Optional[discord.TextChannel]:
    check = await Logging.filter(type=_type, guild_id=guild.id).first()
    if not check:
        return None

    channel = check.channel
    color = check.color

    if not channel:
        return await handle_no_channel(_type, guild)

    else:
        return channel, color


def truncate_string(value, max_length=128, suffix="..."):
    string_value = str(value)
    string_truncated = string_value[: min(len(string_value), (max_length - len(suffix)))]
    suffix = suffix if len(string_value) > max_length else ""
    return string_truncated + suffix
