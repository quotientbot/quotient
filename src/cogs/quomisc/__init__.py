from core import Cog, Quotient, Context
from .dev import *


class Quomisc(Cog, name="quomisc"):
    def __init__(self, bot: Quotient):
        self.bot = bot


def setup(bot):
    bot.add_cog(Quomisc(bot))
    bot.add_cog(Dev(bot))
