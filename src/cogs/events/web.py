from core import Quotient, Cog
from models import Web


class WebEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_scrim_edit_timer_complete(self, payload: Web):
        ...

    @Cog.listener()
    async def on_scrim_create_timer_complete(self, payload: Web):
        ...
