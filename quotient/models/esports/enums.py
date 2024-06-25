from enum import Enum, IntEnum


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


class RegOpenMsgVar(Enum):
    MENTIONS = "Required Mentions for successful registration."
    SLOTS = "Total no of slots in scrim."
    RESERVED = "No of reserved slots"
    MULTIREG = "Whether multiple registrations are allowed."
    START_TIME = "Actual game start time."
    MAP = "Game Map of the day."


class RegCloseMsgVar(Enum):
    SLOTS = "No of total slots in scrim."
    FILLED = "No of slots filled already."
    TIME_TAKEN = "Time taken to finish reg."
    OPEN_TIME = "Next time when the reg will start."
    MAP = "Game Map of the day."
    START_TIME = "Time when game will start."


class SlotlistMsgVar(Enum):
    NAME = "Registration Channel Name"
    TIME_TAKEN = "Time taken to finish reg."
    OPEN_TIME = "Next time when this reg will start."
    MAP = "Game Map of the day."
