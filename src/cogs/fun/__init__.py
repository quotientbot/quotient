from core import Cog, Context, Quotient


class Fun(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot


def setup(bot) -> None:
    bot.add_cog(Fun(bot))
