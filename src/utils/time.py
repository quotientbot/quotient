import datetime as dt


def time(target):
    return target.strftime("%d-%b-%Y %I:%M %p")


def day_today():
    return dt.datetime.now().strftime("%A").lower()
