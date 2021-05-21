from typing import Optional
from utils import LogType
import discord


async def audit_entry(guild, action=None):
    records = await guild.audit_logs(limit=1, action=action, oldest_first=False).flatten()
    return records


async def handle_no_channel(_type: LogType, **kwargs):
    pass


async def handle_no_permission(_type: LogType, **kwargs):
    pass


async def check_permissions(guild: discord.Guild) -> bool:
    pass


async def get_channel(_type: LogType, guild: discord.Guild) -> Optional[discord.TextChannel]:
    pass
