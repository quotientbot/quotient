import re


def find_team_name(content: str) -> str | None:
    """Finds Team Name from a registration msg."""

    team_name_line = re.search(r"team.*", content)
    if team_name_line is None:
        return None

    team_name = re.sub(r"<@*#*!*&*\d+>|team|name|[^\w\s]", "", team_name_line.group()).strip()

    return f"Team {team_name.title()}" if team_name else None
