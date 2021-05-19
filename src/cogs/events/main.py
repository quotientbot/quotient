from core import Cog, Quotient


class MainEvents(Cog, name="Main Events"):
    def __init__(self, bot: Quotient):
        self.bot = bot
