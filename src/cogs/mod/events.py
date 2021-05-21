from core import Cog, Quotient, Context

__all__ = ("ModEvents",)


class ModEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
