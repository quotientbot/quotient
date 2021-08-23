from utils import emote, BaseSelector
from typing import List
from models import Scrim
import discord

__all__ = ("ScrimSelector", "SlotManagerView")


class ScrimSelector(discord.ui.Select):
    def __init__(self, placeholder: str, scrims: List[Scrim]):

        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=scrim.name,
                    value=scrim.id,
                    description=f"{scrim.registration_channel} (ScrimID: {scrim.id})",
                    emoji=emote.category,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class SlotManagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_buttons(self):
        ...

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="cancel-slot", label="Cancel Your Slot")
    async def cancel_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        myview = BaseSelector(
            interaction.user.id,
            ScrimSelector,
            placeholder="select scrim",
            scrims=await Scrim.filter(guild_id=interaction.guild_id),
        )
        await interaction.followup.send("select something", view=myview, ephemeral=True)
        await myview.wait()
        print(myview.custom_id)

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="claim-slot", label="Claim Slot")
    async def claim_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...
