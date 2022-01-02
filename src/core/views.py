from contextlib import suppress
import discord
from core import Context


class QuotientView(discord.ui.View):
    message: discord.Message

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

            with suppress(discord.HTTPException):
                await self.message.edit(embed=self.message.embeds[0], view=self)
