from __future__ import annotations
from datetime import datetime, timedelta

import typing

from models import User

if typing.TYPE_CHECKING:
    from core import Quotient

from constants import IST
from utils import emote
from contextlib import suppress
from core import Context
import discord


class BaseView(discord.ui.View):
    def __init__(self, ctx: Context, *, timeout=30.0):

        self.ctx = ctx
        self.message: discord.Message = None
        self.bot: Quotient = ctx.bot

        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            for b in self.children:
                if isinstance(b, discord.ui.Button) and not b.style == discord.ButtonStyle.link:
                    b.style, b.disabled = discord.ButtonStyle.grey, True

            with suppress(discord.HTTPException):
                await self.message.edit(view=self)


class VoteButton(BaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=None)

        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                url="https://quotientbot.xyz/vote",
                label="Click Here",
            )
        )


class MoneyButton(BaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx)

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="claim_prime", label="Claim Prime (120 coins)")
    async def claim_premium(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        self.children[0].disabled = True
        await self.message.edit(view=self)

        _u = await User.get(pk=self.ctx.author.id)
        if not _u.money >= 120:
            return await interaction.followup.send(
                f"{emote.error} Insufficient Quo Coins in your account.", ephemeral=True
            )

        end_time = (
            _u.premium_expire_time + timedelta(days=30) if _u.is_premium else datetime.now(tz=IST) + timedelta(days=30)
        )

        await User.get(pk=self.ctx.author.id).update(
            is_premium=True, premium_expire_time=end_time, money=_u.money - 120, premiums=_u.premiums + 1
        )
        await self.ctx.success(
            "Credited Quotient Prime for 1 Month to your account,\n\n"
            "Use `qboost` in any server to upgrade it with Prime."
        )
