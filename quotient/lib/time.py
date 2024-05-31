import datetime
import re

import pytz
from discord.ext import commands

TIME_REGEX = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("Asia/Kolkata"))


def convert_to_seconds(argument: str) -> int:
    time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}

    args = argument.lower()
    matches = re.findall(TIME_REGEX, args)
    time = 0
    for key, value in matches:
        try:
            time += time_dict[value] * float(key)
        except KeyError:
            raise commands.BadArgument(
                f"{value} is an invalid time key! h|m|s|d are valid arguments"
            )
        except ValueError:
            raise commands.BadArgument(f"{key} is not a number!")

    return round(time)
