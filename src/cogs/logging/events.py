from core import Quotient, Cog, Context

__all__ = ("LoggingEvents",)


class LoggingEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    async def delete_older_snipes(self):
        pass

    @Cog.listener()
    async def on_snipe_deleted(self, payload):
        pass
