from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from constants import AutocleanType, Day, IST

from datetime import datetime, timedelta

import dateparser
from models import Scrim

__all__ = ("BaseScrim",)


def str_to_time(_t: str):
    parsed = dateparser.parse(
        _t,
        settings={
            "RELATIVE_BASE": datetime.now(tz=IST),
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
    )
    if datetime.now(tz=IST) > parsed:
        parsed = parsed + timedelta(hours=24)

    return parsed


class BaseScrim(BaseModel):
    id: int = None
    guild_id: int
    name: str = "Quotient-Scrims"
    registration_channel_id: int
    slotlist_channel_id: int
    role_id: int
    required_mentions: int
    start_from: int = 1
    total_slots: int
    host_id: int
    open_time: datetime
    autoclean: List[AutocleanType] = list(AutocleanType)
    autoclean_time: datetime = datetime.now(IST).replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(days=1)

    autoslotlist: bool = True
    ping_role_id: int = None
    multiregister: bool = False
    open_role_id: int = None

    autodelete_rejects: bool = False
    autodelete_extras: bool = True
    teamname_compulsion: bool = True

    show_time_elapsed: bool = True
    open_days: List[Day] = list(Day)
    no_duplicate_name: bool = False
    open_message: dict = {}
    close_message: dict = {}

    banlog_channel_id: int = None
    match_time: datetime = None

    # validators
    _open_time = validator("open_time", pre=True)(str_to_time)
    _autoclean_time = validator("autoclean_time", pre=True)(str_to_time)
    _match_time = validator("match_time", pre=True)(str_to_time)

    async def validate_perms(self, bot: Quotient):
        ...

    async def create_scrim(self):
        ...

    async def update_scrim(self):
        ...
