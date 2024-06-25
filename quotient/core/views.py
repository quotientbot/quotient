from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from .bot import Quotient

import discord
from discord.ext import commands
from models import Guild


class QuoView(discord.ui.View):
    message: discord.Message | discord.WebhookMessage
    bot: Quotient | None

    def __init__(
        self,
        ctx: commands.Context | None = None,
        timeout: float = 60.0,
    ):
        super().__init__(timeout=timeout)
        self.ctx = ctx

        if not hasattr(self, "bot"):
            self.bot = Guild.bot

    async def on_timeout(self):
        if not hasattr(self, "message"):
            return

        for b in self.children:
            if isinstance(b, discord.ui.Button) and not b.style == discord.ButtonStyle.link:
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
            embed=self.bot.error_embed("Sorry, you can't use this interaction as it is not started by you."),
            ephemeral=True,
        )
        return False


class PromptView(discord.ui.View):
    view: bool | None

    def __init__(self, user_id: int, confirm_btn_label: str = "Confirm", cancel_btn_label: str = "Cancel"):
        super().__init__(timeout=60.0)

        self.user_id = user_id
        self.value = None

        self.add_item(ConfirmBtn(confirm_btn_label))
        self.add_item(CancelBtn(cancel_btn_label))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if not hasattr(self, "message"):
            return

        for b in self.children:
            if isinstance(b, discord.ui.Button):
                b.style, b.disabled = discord.ButtonStyle.grey, True

        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            pass


class ConfirmBtn(discord.ui.Button):
    view: PromptView

    def __init__(self, label: str, **kwargs):
        super().__init__(style=discord.ButtonStyle.green, label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.value = True
        self.view.stop()


class CancelBtn(discord.ui.Button):
    view: PromptView

    def __init__(self, label: str, **kwargs):
        super().__init__(style=discord.ButtonStyle.red, label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.value = False
        self.view.stop()
