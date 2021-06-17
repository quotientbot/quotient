import pytz
import random
from enum import Enum


class _Sentinel:
    def __repr__(self):
        return "<MISSING>"


class Day(Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class EsportsType(Enum):
    tourney = "tourney"
    scrim = "scrim"


class AutocleanType(Enum):
    channel = "channel"
    role = "role"


class EsportsLog(Enum):
    open = "open"
    closed = "closed"
    success = "reg_success"


class EsportsRole(Enum):
    ping = "ping_role"
    open = "open_role"


class RegDeny(Enum):
    botmention = "mentioned bots"
    nomention = "insufficient mentions"
    banned = "banned"
    multiregister = "multiregiter"
    noteamname = "no_team_name"
    reqperms = "lack_permissions"


class LogType(Enum):
    msg = "msg"  # msg delete / bulk delete / msg edit
    join = "join"  # member join
    leave = "leave"  # mem leave
    action = "action"  # ban , unban
    server = "server"  # server update
    channel = "channel"  # channel create / update
    role = "role"  # role create / update
    member = "member"  # member update
    voice = "voice"  # voice chan logs
    reaction = "reaction"  # reaction stuff
    mod = "mod"  # modlogs case id stuff
    cmd = "cmd"  # bot's cmds
    invite = "invite"  # inv created /deleted (invite tracking alag se ki jayegi)
    ping = "ping"  # someone pinged someone (ye sbse jruri h )


class LockType(Enum):
    channel = "channel"
    guild = "guild"
    category = "category"
    maintenance = "maintenance"


class EventType(Enum):
    meme = "meme"
    fact = "fact"
    quote = "quote"
    joke = "joke"
    nsfw = "nsfw"
    advice = "advice"
    poem = "poem"


perks = {
    "Premium Role": ["❌", "✅"],
    "Scrims": ["3", "Unlimited"],
    "Tourneys": ["2", "Unlimited"],
    "TagCheck": ["1", "Unlimited"],
    "EasyTags": ["1", "Unlimited"],
    "Autorole": ["1", "Unlimited"],
    "Custom Footer": ["❌", "✅"],
    "Custom Color": ["❌", "✅"],
    "Giveaway": ["5", "Unlimited"],
    "Auto-Event Interval": ["❌", "✅"],
}

points = {
    1: 15,
    2: 12,
    3: 10,
    4: 8,
    5: 6,
    6: 4,
    7: 2,
    8: 1,
    9: 1,
    10: 1,
    11: 1,
    12: 1,
    13: 1,
    14: 1,
    15: 1,
    16: 1,
    17: 0,
    18: 0,
    19: 0,
    20: 0,
    21: 0,
    22: 0,
    23: 0,
    24: 0,
    25: 0,
}


def random_greeting():
    greetings = [
        "Hello, sunshine!",
        "Peek-a-boo!",
        "Howdy-doody!",
        "Ahoy, matey!",
        "Hiya!",
        "What’s crackin’?",
        "Howdy, howdy ,howdy!",
        "Yo!",
        "I like your face.",
        "Bonjour!",
        "Yo! You know who this is.",
    ]
    greeting = random.choice(greetings)
    return greeting


MISSING = _Sentinel()
IST = pytz.timezone("Asia/Kolkata")
