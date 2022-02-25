from contextlib import suppress
import discord
from core import Context
from utils import emote

import config

__all__ = ("QuotientView",)


class QuotientView(discord.ui.View):
    message: discord.Message
    custom_id = None

    def __init__(self, ctx: Context, *, timeout=30):
        super().__init__(timeout=timeout)
        self.ctx = ctx

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

                elif isinstance(b, discord.ui.Select):
                    b.disabled = True

            with suppress(discord.HTTPException):
                return await self.message.edit(view=self)

    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        self.ctx.bot.dispatch("command_error", self.ctx, error)

    @staticmethod
    def tricky_invite_button():  # yes lmao
        return discord.ui.Button(emoji=emote.info, url=config.SERVER_LINK)
