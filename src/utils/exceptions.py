from discord.ext import commands


class QuotientError(commands.CheckFailure):
    pass


class NotSetup(QuotientError):
    def __init__(self):
        super().__init__(
            "This command requires you to have Quotient's private channel.\nKindly run `{ctx.prefix}setup` and try again."
        )


class NotPremiumGuild(QuotientError):
    def __init__(self):
        super().__init__(
            "This command requires this server to be premium.\n\nCheckout Quotient Premium [here]({ctx.bot.prime_link})"
        )


class NotPremiumUser(QuotientError):
    def __init__(self):
        super().__init__(
            "This command requires you to be a premium user.\nCheckout Quotient Premium [here]({ctx.bot.prime_link})"
        )


class InputError(QuotientError):
    pass


class SMNotUsable(QuotientError):
    def __init__(self):
        super().__init__(f"You need either the `scrims-mod` role or `Manage Server` permissions to use this command.")


class TMNotUsable(QuotientError):
    def __init__(self):
        super().__init__(f"You need either the `tourney-mod` role or `Manage Server` permissions to use tourney manager.")


class PastTime(QuotientError):
    def __init__(self):
        super().__init__(
            f"The time you entered seems to be in past.\n\nKindly try again, use times like: `tomorrow` , `friday 9pm`"
        )


TimeInPast = PastTime


class InvalidTime(QuotientError):
    def __init__(self):
        super().__init__(f"The time you entered seems to be invalid.\n\nKindly try again.")
