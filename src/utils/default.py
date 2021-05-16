import re
from typing import Union


def find_team(message):
    """Finds team name from a message"""
    content = message.content.lower()
    author = message.author
    teamname = re.search(r"team.*", content)
    if teamname is None:
        return f"{author}'s slot"

    teamname = (re.sub("|team|name|[^\w\s]", "", teamname.group())).strip()

    return f"Team {teamname.title()}" if teamname else f"{author}'s slot"


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
