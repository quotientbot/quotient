from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, validator
from typing import List, TYPE_CHECKING, Tuple, Union

if TYPE_CHECKING:
    from core import Quotient

from constants import AutocleanType, Day, IST

from datetime import datetime, timedelta

import dateparser
from models import Scrim, Guild, Timer

__all__ = ("BaseScrim",)


def str_to_time(_t: str = None):
    if not _t:
        return datetime.now(IST).replace(hour=4, minute=0, second=0, microsecond=0) + timedelta(days=1)

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
    _open_time = validator("open_time", pre=True, allow_reuse=True)(str_to_time)
    _autoclean_time = validator("autoclean_time", pre=True, allow_reuse=True)(str_to_time)
    _match_time = validator("match_time", pre=True, allow_reuse=True)(str_to_time)

    async def validate_perms(self, bot: Quotient) -> Tuple[bool, Union[bool, str]]:
        v = await self.__check_bot_perms(bot)
        if not all(v):
            return v

        guild = bot.get_guild(self.guild_id)

        reg_channel = bot.get_channel(self.registration_channel_id)
        if not reg_channel:
            return False, "Quotient can't see your registration channel. Give Perms."

        _p = reg_channel.permissions_for(guild.me)
        if not all((_p.manage_channels, _p.manage_permissions, _p.manage_messages)):
            return False, "Quotient can't manage this registration channel. Give Perms."

        role = guild.get_role(self.role_id)
        if not role:
            return False, "Quotient couldn't find your sucess role."

        if role >= guild.me.top_role:
            return False, "Drag Quotent role above your success role."

        _p = role.permissions
        if any((_p.administrator, _p.manage_channels, _p.manage_roles, _p.kick_members, _p.ban_members)):
            return False, "Success role has dangerous permissions."

        return True, True

    async def create_scrim(self, bot: Quotient):

        if not await Guild.filter(guild_id=self.guild_id, is_premium=True).exists():
            if await Scrim.filter(guild_id=self.guild_id).count() >= 3:
                return False, "Cannot create more than 3 scrims without Premium."

        if await Scrim.filter(registration_channel_id=self.registration_channel_id).exists():
            return False, "Another scrim is using this registration channel."

        _d = self.dict()
        del _d["id"]

        scrim = await Scrim.create(**_d)

        await bot.reminders.create_timer(scrim.open_time, "scrim_open", scrim_id=scrim.id)

        await bot.reminders.create_timer(scrim.autoclean_time, "autoclean", scrim_id=scrim.id)
        bot.loop.create_task(scrim.setup_logs())
        return True, scrim

    async def update_scrim(self, bot: Quotient):
        scrim = await Scrim.get_or_none(pk=self.id)
        if not scrim:
            return False, "Scrim not found."

        await Timer.filter(extra={"args": [], "kwargs": {"scrim_id": self.id}}, event="autoclean").delete()
        await Timer.filter(extra={"args": [], "kwargs": {"scrim_id": self.id}}, event="scrim_open").delete()
        await bot.reminders.create_timer(self.open_time, "scrim_open", scrim_id=self.id)

        await bot.reminders.create_timer(self.autoclean_time, "autoclean", scrim_id=self.id)

        _d = self.dict()
        del _d["id"]
        del _d["open_days"]
        del _d["autoclean"]

        await Scrim.filter(pk=self.id).update(**_d)

        _w = """UPDATE public."sm.scrims" SET autoclean = $1 , open_days = $2 WHERE id = $3"""
        await bot.db.execute(_w, [_ for _ in self.autoclean], [_ for _ in self.open_days], self.id)

        bot.loop.create_task(scrim.setup_logs())
        return True, True

    async def __check_bot_perms(self, bot: Quotient):

        g = await bot.getch(bot.get_guild, bot.fetch_guild, self.guild_id)

        if g:
            g_perms = g.me.guild_permissions

        if not g:
            return False, "Couldn't find your server. Try again in a few minutes."

        if not all((g_perms.manage_channels, g_perms.manage_roles, g_perms.manage_messages)):
            return False, "Quotient needs manage channels, manage roles permission."

        if not all((g_perms.add_reactions, g_perms.embed_links)):
            return False, "Quotient needs add reacions & embed links permission."

        return True, True
