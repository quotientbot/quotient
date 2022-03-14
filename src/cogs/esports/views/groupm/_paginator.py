from __future__ import annotations
import typing as T

from models.esports.tourney import Tourney, TMSlot

from ..base import EsportsBaseView
from core import Context
import discord


class GroupPages(EsportsBaseView):
    def __init__(self, ctx: Context, tourney: Tourney, *, ping_role=True, category=None):
        super().__init__(ctx)

        self.ping_role = ping_role

        self.tourney = tourney
        self.current_page = 1
        self.total_pages = 0

        self.category: discord.CategoryChannel = category

    # async def render(self):
    #     self.records = await self.tourney._get_groups()
    #     self.record = self.records[0]

    # async def refresh_view(self):
    #     _e = await self.__get_current_page()

    #     try:
    #         self.message = await self.message.edit(embed=_e, view=self)
    #     except discord.HTTPException:
    #         await self.on_timeout()

    # async def __get_current_page(self):
    #     self.records

    async def initial_embed(self, group=1):
        _e = discord.Embed(color=0x00FFB3, title=f"{self.tourney} - Group {group}")
        _e.set_thumbnail(url=getattr(self.ctx.guild.icon, "url", discord.Embed.Empty))

    @discord.ui.button()
    async def prev_button(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def skip_to(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def next_button(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def send_channel(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def send_to(self, button: discord.Button, interaction: discord.Interaction):
        ...
