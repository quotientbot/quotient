from typing import List, Union
from models import Scrim
import discord

from contextlib import suppress
from utils import emote

__all__ = ("ScrimSelectorView",)


class ScrimSelector(discord.ui.Select):
    view: "ScrimSelectorView"

    def __init__(self, placeholder: str, scrims: List[Scrim], max_values=25):

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

        # print(scrims, _options)
        super().__init__(placeholder=placeholder, options=_options, max_values=max_values)

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = self.values

        self.view.stop()


class ScrimSelectorView(discord.ui.View):
    message: discord.Message
    custom_id: List[str] = []

    def __init__(self, user: Union[discord.Member, discord.User], scrims: List[Scrim], **kwargs):
        self.user = user

        timeout = kwargs.get("timeout", 30)
        placeholder = kwargs.get("placeholder", "Select a scrim ...")
        max_values = kwargs.get("max_values", len(scrims))

        super().__init__(timeout=timeout)

        # scrims = scrims[:25]

        self.add_item(ScrimSelector(placeholder, scrims, max_values))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(f"Sorry, only **{self.user}** can use this dropdown.", ephemeral=True)
            return False

        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            with suppress(discord.HTTPException):
                await self.message.delete()


# async def scrim_selector(
#     channel: discord.TextChannel,
#     user: Union[discord.Member, discord.User],
#     scrims: List[Scrim],
#     **kwargs,
# ):


#     if len(scrims) <= 25:
#         view = ScrimSelectorView(user, scrims, **kwargs)
#         view.message = await channel.send("Kindly use the dropdown below to select scrims.", view=view)
#         await view.wait()
#         return await Scrim.filter(pk__in=view.custom_id).order_by("id")
