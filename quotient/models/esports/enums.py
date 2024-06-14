from enum import IntEnum


class Day(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class IdpShareType(IntEnum):
    LEADER_ONLY = 0
    ALL_TEAM_MEMBERS = 1
