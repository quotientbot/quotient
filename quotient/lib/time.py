import datetime

import pytz


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
