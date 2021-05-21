import re
from typing import Union
from datetime import datetime

from .constants import IST


def find_team(message):
    """Finds team name from a message"""
    content = message.content.lower()
    author = message.author
    teamname = re.search(r"team.*", content)
    if teamname is None:
        return f"{author}'s team"

    teamname = (re.sub(r"\b[0-9]+\b\s*|team|name|[^\w\s]", "", teamname.group())).strip()

    return f"Team {teamname.title()}" if teamname else f"{author}'s team"


def regional_indicator(c: str) -> str:
    """Returns a regional indicator emoji given a character."""
    return chr(0x1F1E6 - ord("A") + ord(c.upper()))


def keycap_digit(c: Union[int, str]) -> str:
    """Returns a keycap digit emoji given a character."""
    c = int(c)
    if 0 < c < 10:
        return str(c) + "\U0000FE0F\U000020E3"
    elif c == 10:
        return "\U000FE83B"
    raise ValueError("Invalid keycap digit")


async def aenumerate(asequence, start=0):
    """Asynchronously enumerate an async iterator from a given start value"""
    n = start
    async for elem in asequence:
        yield n, elem
        n += 1


def get_ipm(bot):
    """Returns Quotient's cmds invoke rate per minute"""
    time = (datetime.now(tz=IST) - bot.start_time).total_seconds()
    per_second = bot.cmd_invokes / time
    per_minute = per_second * 60
    return per_minute
