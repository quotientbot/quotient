from __future__ import annotations
import typing as T

from ..base import EsportsBaseView
from core import Context
import discord


class GroupPages(EsportsBaseView):
    def __init__(self, ctx: Context, *, ping_role=True, category=None):
        super().__init__(ctx)

        self.ping_role = ping_role
        self.current_page = 1

        self.category: discord.CategoryChannel = category

    async def render(self):
        ...

    async def get_page(self):
        ...

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
