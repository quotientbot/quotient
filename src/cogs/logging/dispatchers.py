from core import Quotient, Cog, Context

__all__ = ("LoggingDispatchers",)


class LoggingDispatchers(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
