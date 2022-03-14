from __future__ import annotations
from contextlib import suppress
import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from core import Cog
import discord

from constants import random_greeting, random_thanks

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
        if not data.get("is_verified"):
            return await self.__transaction_failed(int(u))

        await self.bot.sio.emit("new_premium__{0}".format(u), {})

        user_id = int(u)
        invoice = data["invoice_link"]

        prime = "https://discord.com/oauth2/authorize?client_id=902856923311919104&scope=applications.commands%20bot&permissions=21175985838"

        member = self.bot.server.get_member(user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE), reason="They purchased premium.")

        else:
            member = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)

        _e = discord.Embed(color=self.bot.color)
        _e.description = (
            f"{random_greeting()} {member.mention},\n"
            "Thanks for purchasing Quotient Premium.\n\n"
            f"[Invite Prime Bot]({prime}) | [Support Server]({self.bot.config.SERVER_LINK}) | [Download Invoice]({invoice})"
        )

        _e.set_image(url=random_thanks())

        with suppress(discord.HTTPException, AttributeError):
            await member.send(embed=_e)

    async def __transaction_failed(self, user_id: int):
        # user = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)
        # if user:
        #     with suppress(discord.HTTPException):
        #         await user.send(
        #             embed=discord.Embed()
        #         )

        ...
