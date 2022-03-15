from __future__ import annotations

import typing as T
from models import Tourney, TGroupList
import discord


class GroupRefresh(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(custom_id="t_groups_refresh", emoji="<:refresh:953334999891988480>")
    async def refresh_group(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        record = await TGroupList.get_or_none(pk=interaction.message.id, channel_id=interaction.channel_id)
        if not record:
            self.children[0].disabled = True
            return await interaction.edit_original_message(view=self)
