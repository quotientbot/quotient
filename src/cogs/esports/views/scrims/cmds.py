from __future__ import annotations

from core import Context
from ...views.base import EsportsBaseView

import discord


class ScrimsCommands(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx)

        self.ctx = ctx

    async def initial_message(self):
        ...

    @discord.ui.button(label="Create New", style=discord.ButtonStyle.blurple, custom_id="c_new_scrim")
    async def create_new_scrim(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.green, custom_id="c_edit_scrim")
    async def edit_scrim(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Slotlist Settings", style=discord.ButtonStyle.blurple, custom_id="c_slotlist_settings")
    async def slotlist_settings(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Scrim Settings", style=discord.ButtonStyle.blurple, custom_id="c_scrim_settings")
    async def scrim_settings(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Reserve Slots", style=discord.ButtonStyle.blurple, custom_id="c_reserve_slots")
    async def reserve_slots(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Ban/Unban", style=discord.ButtonStyle.blurple, custom_id="c_ban_unban")
    async def ban_unban(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Start Reg", style=discord.ButtonStyle.blurple, custom_id="c_start_reg")
    async def start_reg(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="End Reg", style=discord.ButtonStyle.blurple, custom_id="c_end_reg")
    async def end_reg(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, custom_id="c_delete_scrim")
    async def delete_scrim(self, button: discord.Button, interaction: discord.Interaction):
        ...
