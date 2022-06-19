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
        self.hook = discord.Webhook.from_url(self.bot.config.PUBLIC_LOG, session=self.bot.session)
        # self.flantic_hook = discord.Webhook.from_url(self.bot.config.FLANTIC_PREMIUM, session=self.bot.session)

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
                "Real Bot Premium for 1 Month (worth $5)",
            ],
        )

    @Cog.listener()
    async def on_request__new_premium(self, u, data: dict):
        await self.bot.sio.emit("new_premium__{0}".format(u), {})

        if not data.get("is_verified"):
            return await self.__transaction_failed(int(u))

        user_id = int(u)
        invoice = data["invoice_link"]

        prime = "https://discord.com/oauth2/authorize?client_id=902856923311919104&scope=applications.commands%20bot&permissions=536737213566"

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

            if data["details"]["amount"] != "29.00":
                # await self.ping_flantic(user_id)
                await self.give_real(member)

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

    async def give_real(self, member: discord.Member | discord.User):
        async with self.bot.session.get(self.bot.config.REAL_PREMIUM + str(member.id)) as res:
            if not res.status == 200:
                return

            res = await res.json()

            _f = discord.Embed(color=self.bot.color, title="Quotient x RealMusic", url=self.bot.config.SERVER_LINK)
            _f.description = (
                "Quotient has partnered with Real, An Extraordinary Music Bot With Slash Commands, "
                "Spotify Support, DJ System, Request Channel, And Much More!\n\n"
                "With your Quotient Prime purchase, you have received **One Month Premium of Real Bot.**"
                "\n\n__Please follow these steps:__\n"
                "1. [Invite Real Music Bot](https://top.gg/bot/802812378558889994)\n"
                "2. Use `!!redeem {0}` in your server.".format(res["code"])
            )

            _f.set_thumbnail(
                url="https://media.discordapp.net/attachments/925259723379449908/941281803677892658/reals.png"
            )

            with suppress(discord.HTTPException):
                await member.send(embed=_f)

    # async def ping_flantic(self, user_id):
    #     await self.flantic_hook.send(content=user_id)
