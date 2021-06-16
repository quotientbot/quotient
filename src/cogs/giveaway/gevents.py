from core import Cog, Context, Quotient
from models import Timer


class Gevents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_giveaway_timer_complete(self, timer: Timer):
        pass
