from __future__ import annotations
import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from core import Cog

__all__ = ("SockPrime",)


class SockPrime(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_request__perks(self, u, data):
        return await self.bot.sio.emit(
            f"perks__{u}",
            [
                "Unlimited Scrims (3 for free)",
                "Unlimited tournaments (1 for free)",
                "Unlimited tagcheck and easytag channels.",
                "Custom reactions for tourney and scrims.",
                "Unlimited media partner channels.",
                "Unlimited ssverification channels.",
                "Premium role in our server + several other benefits...",
            ],
        )

    @Cog.listener()
    async def on_request__new_premium(self, u, data: dict):
        user_id = int(data["user_id"])
