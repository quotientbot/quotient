from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class SockTourney(BaseModel):
    id: Optional[int] = None
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
    open_role_id: Optional[int] = None
    teamname_compulsion: bool = False
    ping_role_id: Optional[int] = None
    no_duplicate_name: bool = True
    autodelete_rejected: bool = True
    success_message: Optional[str] = None
