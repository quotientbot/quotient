from core import Cog, Quotient, Context


class Premium(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


def setup(bot) -> None:
    bot.add_cog(Premium(bot))
