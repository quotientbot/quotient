import datetime as dtm
import re

import dateparser
import parsedatetime as pdt
from dateutil.parser import ParserError, parse
from dateutil.relativedelta import relativedelta
from discord.ext import commands

from constants import IST
from core import Context
from utils import exceptions

from .formats import plural
from .regex import TIME_REGEX

units = pdt.pdtLocales["en_US"].units


class PastDate(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            dt = parse(argument, ignoretz=True)
        except ParserError:
            raise commands.BadArgument(
                "The date format you entered seems to be Invalid.\n\n"
                "The day can be human readable date like `11 May` or maybe a more concrete one such as '4-05-2021'"
            )

        else:
            if dt.date() > dtm.datetime.now().date():
                raise commands.BadArgument(
                    "This date seems to be in future, either write today's date or some date that is in past."
                )

            return IST.localize(dt.replace(hour=0, minute=0, second=0, microsecond=0))


class ShortTime:
    compiled = re.compile(
        """(?:(?P<years>[0-9])(?:years?|y))?             # e.g. 2y
                             (?:(?P<months>[0-9]{1,2})(?:months?|mo))?     # e.g. 2months
                             (?:(?P<weeks>[0-9]{1,4})(?:weeks?|w))?        # e.g. 10w
                             (?:(?P<days>[0-9]{1,5})(?:days?|d))?          # e.g. 14d
                             (?:(?P<hours>[0-9]{1,5})(?:hours?|h))?        # e.g. 12h
                             (?:(?P<minutes>[0-9]{1,5})(?:minutes?|m))?    # e.g. 10m
                             (?:(?P<seconds>[0-9]{1,5})(?:seconds?|s))?    # e.g. 15s
                          """,
        re.VERBOSE,
    )

    def __init__(self, argument, *, now=None):
        match = self.compiled.fullmatch(argument)
        if match is None or not match.group(0):
            raise exceptions.InvalidTime()

        data = {k: int(v) for k, v in match.groupdict(default=0).items()}
        now = dtm.datetime.now(tz=IST)
        self.dt = now + relativedelta(**data)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls(argument, now=dtm.datetime.now(tz=IST))


class HumanTime:
    calendar = pdt.Calendar(version=pdt.VERSION_CONTEXT_STYLE)

    def __init__(self, argument, *, now=None):
        now = now or dtm.datetime.now(tz=IST)
        dt, status = self.calendar.parseDT(argument, sourceTime=now)
        if not status.hasDateOrTime:
            raise exceptions.InvalidTime()

        dt = dt.replace(tzinfo=IST)

        if not status.hasTime:
            # replace it with the current time
            dt = dt.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)

        self.dt = dt
        self._past = dt < now

    @classmethod
    async def convert(cls, ctx, argument):
        return cls(argument, now=ctx.message.created_at)


class Time(HumanTime):
    def __init__(self, argument, *, now=None):
        try:
            o = ShortTime(argument, now=now)
        except Exception as e:
            super().__init__(argument)
        else:
            self.dt = o.dt
            self._past = False


class FutureTime(Time):
    def __init__(self, argument, *, now=None):
        super().__init__(argument, now=dtm.datetime.now(tz=IST))

        if self._past:
            raise exceptions.PastTime()


class BetterFutureTime:
    @classmethod
    async def convert(cls, ctx, argument: str):
        if not "in" in argument:
            argument = "in " + argument

        parsed = dateparser.parse(
            argument,
            settings={
                "RELATIVE_BASE": dtm.datetime.now(tz=IST),
                "TIMEZONE": "Asia/Kolkata",
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )
        if not parsed:
            raise exceptions.InvalidTime()

        if dtm.datetime.now(tz=IST) > parsed:
            parsed = parsed + dtm.timedelta(hours=24)

        if parsed < dtm.datetime.now(tz=IST):
            raise exceptions.PastTime()

        return parsed


def time(target):
    return target.strftime("%d-%b-%Y %I:%M %p")


def day_today():
    return dtm.datetime.now().strftime("%A").lower()


def strtime(target):
    return target.strftime("%d-%b-%Y %I:%M %p")


def discord_timestamp(time_to_convert, mode="R"):
    formated_strftime = f"<t:{int(time_to_convert.timestamp())}:{mode}>"

    return formated_strftime


# def strtime(target):
#     return f"<t:{int(target.timestamp())}:R>"


def human_join(seq, delim=", ", final="or"):
    size = len(seq)
    if size == 0:
        return ""

    if size == 1:
        return seq[0]

    if size == 2:
        return f"{seq[0]} {final} {seq[1]}"

    return delim.join(seq[:-1]) + f" {final} {seq[-1]}"


def human_timedelta(dt, *, source=None, accuracy=3, brief=False, suffix=True):
    now = source or dtm.datetime.now(tz=IST)
    # Microsecond free zone
    now = now.replace(microsecond=0)
    dt = dt.replace(microsecond=0)

    # This implementation uses relativedelta instead of the much more obvious
    # divmod approach with seconds because the seconds approach is not entirely
    # accurate once you go over 1 week in terms of accuracy since you have to
    # hardcode a month as 30 or 31 days.
    # A query like "11 months" can be interpreted as "!1 months and 6 days"
    if dt > now:
        delta = relativedelta(dt, now)
        suffix = ""
    else:
        delta = relativedelta(now, dt)
        suffix = " ago" if suffix else ""

    attrs = [
        ("year", "y"),
        ("month", "mo"),
        ("day", "d"),
        ("hour", "h"),
        ("minute", "m"),
        ("second", "s"),
    ]

    output = []
    for attr, brief_attr in attrs:
        elem = getattr(delta, attr + "s")
        if not elem:
            continue

        if attr == "day":
            weeks = delta.weeks
            if weeks:
                elem -= weeks * 7
                if not brief:
                    output.append(format(plural(weeks), "week"))
                else:
                    output.append(f"{weeks}w")

        if elem <= 0:
            continue

        if brief:
            output.append(f"{elem}{brief_attr}")
        else:
            output.append(format(plural(elem), attr))

    if accuracy is not None:
        output = output[:accuracy]

    if len(output) == 0:
        return "now"
    if not brief:
        return human_join(output, final="and") + suffix
    return " ".join(output) + suffix


time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


def simple_convert(argument):
    args = argument.lower()
    matches = re.findall(TIME_REGEX, args)
    time = 0
    for key, value in matches:
        try:
            time += time_dict[value] * float(key)
        except KeyError:
            raise commands.BadArgument(f"{value} is an invalid time key! h|m|s|d are valid arguments")
        except ValueError:
            raise commands.BadArgument(f"{key} is not a number!")

    return round(time)


class TimeText(commands.Converter):
    def __init__(self, converter=None):
        self.converter = converter

    def __final_checks(self, dt, remaining=None):
        self.arg = remaining
        if remaining and remaining.strip() == "":
            self.arg = None

        self.dt = dt
        if self.dt:
            while self.dt < dtm.datetime.now():
                self.dt += dtm.timedelta(days=1)

            self.dt = IST.localize(self.dt)
        return self

    async def convert(self, ctx: Context, argument: str):
        try:
            calendar = HumanTime.calendar
            regex = ShortTime.compiled
            now = dtm.datetime.now()

            match = regex.match(argument)
            if match is not None and match.group(0):
                data = {k: int(v) for k, v in match.groupdict(default=0).items()}
                remaining = argument[match.end() :].strip()
                dt = now + relativedelta(**data)

                return self.__final_checks(dt, remaining)

            if argument.endswith("from now"):
                argument = argument[:-8].strip()

            if argument[0:2] == "me":
                # starts with "me to", "me in", or "me at "
                if argument[0:6] in ("me to ", "me in ", "me at "):
                    argument = argument[6:]

            elements = calendar.nlp(argument, sourceTime=now)
            if elements is None or len(elements) == 0:
                return self.__final_checks(None, argument)

            dt, status, begin, end, dt_string = elements[0]

            if begin in (0, 1):
                if begin == 1:
                    remaining = argument[end + 1 :].lstrip(" ,.!")
                else:
                    remaining = argument[end:].lstrip(" ,.!")

            elif len(argument) == end:
                remaining = argument[:begin].strip()

            if not status.hasDateOrTime:
                return self.__final_checks(None, remaining)

            if status.accuracy == pdt.pdtContext.ACU_HALFDAY:
                dt = dt.replace(day=now.day + 1)

            return self.__final_checks(dt, remaining)

        except:
            import traceback

            traceback.print_exc()
            raise
