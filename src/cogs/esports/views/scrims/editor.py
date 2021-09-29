from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView
from core import Context
from models import Scrim

from utils import regional_indicator as ri, inputs, truncate_string

import discord


class ScrimEditor(EsportsBaseView):
    def __init__(self, ctx: Context, *, scrim: Scrim):
        super().__init__(ctx, timeout=60, title="Scrims Editor")

        self.ctx = ctx
        self.scrim = scrim

        self.bot: Quotient = ctx.bot

    @staticmethod
    def initial_message(scrim: Scrim) -> discord.Embed:
        
        embed = discord.Embed(color=0x00FFB3, title=f"Scrim Editor (ID: {scrim.id})")
    

    async def __update_scrim(self, **kwargs):
        await Scrim.filter(pk=self.scrim.id).update(**kwargs)
        await self.__refresh_view()

    async def __refresh_view(self):
        await self.scrim.refresh_from_db()
        embed = self.initial_message(self.scrim)

        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="scrim_name", emoji=ri("a"), row=1)
    async def set_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        msg = await self.ask_embed(
            "What should be the new name of this scrim?\n\n" "`Please Keep this under 30 characters.`"
        )

        new_name = await inputs.string_input(self.ctx, self.check, delete_after=True)

        new_name = truncate_string(new_name.strip(), 30)

        await self.ctx.safe_delete(msg)

        await self.__update_scrim(name=new_name)
