from discord.ext import commands


class NotSetup(commands.CheckFailure):
    pass


class NotPremiumGuild(commands.CheckFailure):
    pass


class NotPremiumUser(commands.CheckFailure):
    pass


class InputError(commands.CommandError):
    pass


class SMNotUsable(commands.CheckFailure):
    pass


class TMNotUsable(commands.CheckFailure):
    pass


class PastTime(commands.CheckFailure):
    pass


class InvalidTime(commands.CheckFailure):
    pass
