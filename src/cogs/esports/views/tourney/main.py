from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Context
from ..base import EsportsBaseView

from ._wiz import TourneySetupWizard
import discord

from models import Tourney


class TourneyManager(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100, name="Tourney Manager")
        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    async def initial_embed(self) -> discord.Embed:
        to_show = [
            f"`{idx}.` {str(_r)}"
            for idx, _r in enumerate(await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id"), start=1)
        ]

        _e = discord.Embed(color=self.bot.color, title="Smart Tournament Manager", url=self.bot.config.SERVER_LINK)
        _e.description = "\n".join(to_show) if to_show else "```Click Create button for new tourney.```"
        _e.set_thumbnail(url=self.ctx.guild.me.avatar.url)
        _e.set_footer(
            text="Quotient Prime allows unlimited tournaments.",
            icon_url=getattr(self.ctx.author.avatar, "url", discord.Embed.Empty),
        )
        return _e

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="create_tourney", label="Create Tournament")
    async def create_tournament(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        _v = TourneySetupWizard(self.ctx)
        _v.message = await self.ctx.send(embed=_v.initial_message(), view=_v)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="edit_tourney", label="Edit Settings")
    async def edit_tournament(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
