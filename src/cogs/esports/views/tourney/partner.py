from ...views.base import EsportsBaseView
from models import Tourney, MediaPartner

from core import Context
import discord


class MediaPartnerView(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney):
        super().__init__(ctx, timeout=60, title="Tourney Media Partner")
        self.tourney = tourney
        self.ctx = ctx

    @staticmethod
    def initial_embed(ctx: Context, tourney: Tourney) -> discord.Embed:
        return discord.Embed(description="hi bro")

    async def __refresh_embed(self):
        await self.tourney.refresh_from_db()

        embed = self.initial_embed(self.ctx, self.tourney)
        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="add_media_partner", label="Add Media Partner")
    async def add_partner(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="edit_tourney_partner", label="Edit Partner")
    async def edit_partner(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(
        style=discord.ButtonStyle.secondary, custom_id="remove_media_partner", label="Remove Media Partner", row=2
    )
    async def remove_partner(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="stop_partner_view", emoji="❌", row=2)
    async def remove_partner_view(self, button: discord.Button, interaction: discord.Interaction):
        await self.on_timeout()
