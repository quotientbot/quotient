from __future__ import annotations

import typing as T

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
                "Remind Me & Transfer Id-Pass button in Scrims Slotm.",
                "Unlimited tagcheck and easytag channels.",
                "Custom reactions for tourney and scrims.",
                "Unlimited media partner channels.",
                "Unlimited ssverification channels.",
                "Rilp Bot Premium for 1 Month.",
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

        prime = "https://discord.com/oauth2/authorize?client_id=902856923311919104&scope=applications.commands%20bot&permissions=536737213566"

        member = await self.bot.get_or_fetch_member(self.bot.server, user_id)
        if member is not None:
            await member.add_roles(discord.Object(id=self.bot.config.PREMIUM_ROLE), reason="They purchased premium.")

        else:
            member = await self.bot.getch(self.bot.get_user, self.bot.fetch_user, user_id)

        _e = discord.Embed(color=self.bot.color)
        _e.description = (
            f"{random_greeting()} {member.mention},\n"
            "Thanks for purchasing Quotient Premium.\n\n"
            f"[Invite Quotient Pro]({prime}) | [Support Server]({self.bot.config.SERVER_LINK}) | [Download Invoice]({invoice})"
        )

        _e.set_image(url=random_thanks())

        try:
            await member.send(embed=_e)
        except discord.HTTPException:
            pass

        if data["details"]["amount"] != "29.00":
            await self.give_rilp_premium(member)

        _e = discord.Embed(
            color=discord.Color.gold(), description=f"Thanks **{member}** for purchasing Quotient Premium."
        )
        _e.set_image(url=random_thanks())
        await self.hook.send(embed=_e, username="premium-logs", avatar_url=self.bot.config.PREMIUM_AVATAR)

    async def __transaction_failed(self, user_id: int) -> None:
        ...

    async def give_rilp_premium(self, member: discord.Member | discord.User) -> None:

        async with self.bot.session.post(
            self.bot.config.RILP_PREMIUM,
            headers=self.bot.config.RILP_HEADERS,
            json={"userId": member.id, "subscriptionId": "Q_{}".format(self.bot.current_time.timestamp())},
        ) as res:
            if not res.status == 200:
                return

            res = await res.json()
            _f = discord.Embed(color=self.bot.color, title="Quotient x RILP BOT", url=self.bot.config.SERVER_LINK)
            _f.description = (
                "Quotient has partnered with Rilp Bot, a multipurpose bot that features Automoderation, "
                "Invite Tracking, Starboard, Welcome and Leave messages, Giveaways, Polls, Moderation, "
                "Captcha Security, and much more.\n\n"
                "With this Quotient Pro purchase, you have received **Rilp Bot Premium (30 days)**"
                "\n\n__Please follow these steps:__\n"
                "➜ Head over to dashboard <https://rilp-bot.tech>\n"
                "➜ Login with your discord account from which you bought Quotient Pro.\n"
                "➜ Click on the dropdown beside avatar and then head over to `Manage Subscription`\n"
                "➜ Click on 'Select Server' and choose your server to activate premium.\n\n"
                "To Invite RILP BOT - <https://rilp-bot.tech/invite>\n"
                "Dashboard - https://rilp-bot.tech\n"
                "Support Server - <https://rilp-bot.tech/support>\n"
            )

            _f.set_image(
                url="https://cdn.discordapp.com/attachments/1001770455016935536/1002246506981625947/rilpxquotient.jpg"
            )
            try:
                await member.send(embed=_f)

            except discord.Forbidden:
                return
