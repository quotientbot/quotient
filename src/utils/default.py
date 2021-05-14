import re
import unicodedata
from typing import Union




def find_team(matched):
    team_name = [x for x in matched[0].lower().split() if x not in {"team", "name"}]
    team_name = " ".join([i for i in team_name if all(ch not in i for ch in ["@"])])
    team_name = re.sub(r"[^\w\s]", "", team_name)

    return unicodedata.normalize("NFKC", team_name.replace("name", ""))


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


