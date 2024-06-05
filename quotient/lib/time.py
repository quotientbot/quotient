import datetime
import re

import dateparser
import pytz
from discord.ext import commands

TIME_REGEX = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")


def get_today_day() -> int:
    """
    Returns the current day of the week.
    """
    return datetime.datetime.now(pytz.timezone("Asia/Kolkata")).weekday()


def get_current_time() -> datetime.datetime:
    """
    Returns the current time in Asia/Kolkata timezone.
    """
    return datetime.datetime.now(pytz.timezone("Asia/Kolkata"))


def convert_to_seconds(argument: str) -> int:
    """
    Convert a time string like 1h, 3m, 5s, 2d to seconds.
    """
    time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}

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


def parse_natural_time(natural_time: str) -> datetime.datetime | None:
    """
    Parse a natural time string to a datetime object.
    """
    try:
        parsed = dateparser.parse(
            natural_time,
            settings={
                "TIMEZONE": "Asia/Kolkata",
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )

        while get_current_time() > parsed:
            parsed += datetime.timedelta(hours=24)

        return parsed

    except TypeError as e:
        raise e
