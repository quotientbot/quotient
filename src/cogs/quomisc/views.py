from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

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
                await self.message.edit(embed=self.message.embeds[0], view=self)


class VoteButton(BaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=None)

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                url="https://quotientbot.xyz/vote",
                label="Click Here",
            )
        )
