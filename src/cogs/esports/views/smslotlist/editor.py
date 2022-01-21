from __future__ import annotations


from core import Context
import discord

from models import Scrim


__all__ = ("ScrimsSlotlistEditor",)


class ScrimsSlotlistEditor(discord.ui.View):
    message: discord.Message

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(timeout=None)

        self.ctx = ctx
        self.scrim = scrim

    async def on_timeout(self) -> None:
        if not hasattr(self, "message"):
            return

        for _ in self.children:
            if isinstance(_, discord.Button):
                _.disabled = True

        return self.message.edit(embed=self.message.embeds[0], view=self)

    @discord.ui.button(style=discord.ButtonStyle.success, label="Change Team", custom_id="smslot_change_team")
    async def change_team_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        

    @discord.ui.button(style=discord.ButtonStyle.success, label="Add Slot", custom_id="smslot_add_team")
    async def add_team_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Team", custom_id="smslot_remove_team")
    async def remove_team_name(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
