from core import Cog, Quotient, Context


class Utility(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


def setup(bot):
    bot.add_cog(Utility(bot))
