import pytz
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


MISSING = _Sentinel()
IST = pytz.timezone("Asia/Kolkata")
