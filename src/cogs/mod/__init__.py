from core import Cog, Quotient, Context
from .events import *


class Mod(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


def setup(bot):
    bot.add_cog(Mod(bot))
    bot.add_cog(ModEvents(bot))
