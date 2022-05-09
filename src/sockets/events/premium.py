from __future__ import annotations

import typing as T
from contextlib import suppress

if T.TYPE_CHECKING:
    from core import Quotient

import discord

from constants import random_greeting, random_thanks
from core import Cog

__all__ = ("SockPrime",)


class SockPrime(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
        self.hook = discord.Webhook.from_url(self.bot.config.PUBLIC_LOG, session=self.bot.session)

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
        await self.bot.sio.emit("new_premium__{0}".format(u), {})

        if not data.get("is_verified"):
            return await self.__transaction_failed(int(u))

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

        _e = discord.Embed(
            color=discord.Color.gold(), description=f"Thanks **{member}** for purchasing Quotient Premium."
        )
        _e.set_image(url=random_thanks())
        await self.hook.send(embed=_e, username="premium-logs", avatar_url=self.bot.config.PREMIUM_AVATAR)

    async def __transaction_failed(self, user_id: int):
        # user = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)
        # if user:
        #     with suppress(discord.HTTPException):
        #         await user.send(
        #             embed=discord.Embed()
        #         )

        ...
