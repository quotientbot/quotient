from typing import List

from pydantic import BaseModel


class SockTourney(BaseModel):
    id: int = None
    guild_id: int
    name: str = "Quotient-Tourney"
    registration_channel_id: int
    confirm_channel_id: int
    role_id: int
    required_mentions: int = 4
    total_slots: int
    banned_users: List[int]
    host_id: int
    multiregister: bool = False
    open_role_id: int = None
    teamname_compulsion: bool = False
    ping_role_id: int = None
    no_duplicate_name: bool = True
    autodelete_rejected: bool = True
    success_message: str = None
