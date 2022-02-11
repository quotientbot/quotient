from datetime import datetime
from pydantic import BaseModel, validator
from typing import List

from constants import AutocleanType, Day, IST

from datetime import datetime, timedelta


def str_to_time(_t: str):
    ...


class BaseScrim(BaseModel):
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
