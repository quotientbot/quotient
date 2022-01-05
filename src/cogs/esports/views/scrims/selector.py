from typing import List, Union
from models import Scrim
import discord

from contextlib import suppress
from utils import emote

__all__ = ("ScrimSelectorView",)


class ScrimSelector(discord.ui.Select):
    view: "ScrimSelectorView"

    def __init__(self, placeholder: str, scrims: List[Scrim]):

        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=scrim.registration_channel.name,  # type: ignore
                    value=scrim.id,
                    description=f"{scrim.name} (ScrimID: {scrim.id})",
                    emoji=emote.TextChannel,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class ScrimSelectorView(discord.ui.View):
    message: discord.Message
    custom_id: str

    def __init__(self, user: Union[discord.Member, discord.User], scrims: List[Scrim], *, timeout=30.0):
        self.user = user

        super().__init__(timeout=timeout)

        _1, _2 = scrims[:25], scrims[25:]

        self.add_item(ScrimSelector("Select a scrim ...", _1))

        if _2:
            self.add_item(ScrimSelector("Select a scrim ...", _2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(f"Sorry, only **{self.user}** can use this dropdown.", ephemeral=True)
            return False

        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            with suppress(discord.HTTPException):
                await self.message.delete()
