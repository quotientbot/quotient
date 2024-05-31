from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from .bot import Quotient

import discord
from discord.ext import commands


class QuoView(discord.ui.View):
    message: discord.Message

    def __init__(
        self,
        bot: Quotient,
        ctx: commands.Context | None = None,
        timeout: float = 60.0,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = bot

    async def on_timeout(self):
        if not hasattr(self, "message"):
            return

        for b in self.children:
            if (
                isinstance(b, discord.ui.Button)
                and not b.style == discord.ButtonStyle.link
            ):
                b.style, b.disabled = discord.ButtonStyle.grey, True

            elif isinstance(b, discord.ui.Select):
                b.disabled = True

        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.ctx:
            return True

        if interaction.user.id == self.ctx.author.id:
            return True

        await interaction.response.send_message(
            embed=self.bot.error_embed(
                "Sorry, you can't use this interaction as it is not started by you."
            ),
            ephemeral=True,
        )
        return False
