from core import Quotient, Cog, Context
from .dispatchers import *
from .events import *


class Logging(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


def setup(bot):
    bot.add_cog(Logging(bot))
    bot.add_cog(LoggingDispatchers(bot))
    bot.add_cog(LoggingEvents(bot))
