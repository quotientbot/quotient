from utils import emote
from typing import List
from models import Scrim
import discord


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
