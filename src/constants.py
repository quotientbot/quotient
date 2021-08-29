from contextlib import suppress
import pytz, discord
import config
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


class PremiumPurchase(Enum):
    GIFT = "gift"
    PARTNERSHIP = "partner"
    SHOP = "shop"
    REGULAR = "regular"


class PartnerRequest(Enum):
    pending = "1"
    approved = "2"
    denied = "3"


class EsportsType(Enum):
    tourney = "tourney"
    scrim = "scrim"


class AutocleanType(Enum):
    channel = "channel"
    role = "role"


class SSStatus(Enum):
    approved = "approved"
    disapproved = "disapproved"


class VerifyImageError(Enum):
    Invalid = "InvalidScreenshot"
    NotSame = "NotSame"
    NoFollow = "NotFollowed"


class SSType(Enum):
    yt = "youtube"
    insta = "instagram"


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
    multiregister = "multiregister"
    noteamname = "no_team_name"
    reqperms = "lack_permissions"
    duplicate = "duplicate_name"
    bannedteammate = "banned_teammate"


class RegMsg(Enum):
    sopen = "Scrim Registration Open"
    sclose = "Scrim Registration Close"
    topen = "Tourney Registration Open"
    tclose = "Tourney Registration Close"


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


class ScrimBanType(Enum):
    ban = "banned"
    unban = "unbanned"


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
    "Ptable Setup": ["2", "Unlimited"],
    "Edit Ptable Watermark": ["❌", "✅"],
    "Autopurge": ["1", "Unlimited"],
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
    return random.choice(greetings)


def random_thanks():
    msges = (
        "https://cdn.discordapp.com/attachments/877888851241238548/877890130478784532/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877890377426821140/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877890550399918122/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891011349725194/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891209421549628/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891348869550100/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891767058444359/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877891874671706162/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/877892011720572988/unknown.png",
        "https://cdn.discordapp.com/attachments/829953427336593429/878898567509573652/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/881575840578695178/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/881576005498732625/unknown.png",
        "https://cdn.discordapp.com/attachments/877888851241238548/881576299137761350/unknown.png",
    )
    return random.choice(msges)


tips = (
    "You can use `automemes #channel` to setup automemes with Quotient for free.",
    "You can setup unlimited scrims & tourneys with Quotient Premium:\nhttps://quotientbot.xyz/premium",
    "You can create unlimited giveaways with Quotient Premium:\nhttps://quotientbot.xyz/premium",
    "We have an awesome support server:\ndiscord.gg/quotient",
    "I like your face : )",  # I really do
    "You can get a list of Quotient premium perks with `perks` command.",
    "You can customize scrim slotlist designs with `sm slotlist format` command.",
    "You can add a role to multiple users with `role @role @user @user2...` command.",
    "You can look into my source code, use `source` command.",
)


async def show_tip(ctx):
    if ctx.author.id in config.DEVS or ctx.guild.id == config.SERVER_ID:
        return

    if random.randint(10, 69) == 69:
        with suppress(discord.HTTPException, discord.Forbidden):
            await ctx.send(f"**Did You Know?:** {random.choice(tips)}", delete_after=10)


class HelpGIF(Enum):
    pass


MISSING = _Sentinel()
IST = pytz.timezone("Asia/Kolkata")
