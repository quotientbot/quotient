from typing import NamedTuple, Union, List
import discord
from .default import split_list
from .emote import TextChannel, VoiceChannel


class LinkType(NamedTuple):
    name: str
    url: str


class LinkButton(discord.ui.View):
    def __init__(self, links: list):
        super().__init__()

        for link in links:
            self.add_item(discord.ui.Button(label=link.name, url=link.url))


class Prompt(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30.0)
        self.user_id = user_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()


class BaseSelector(discord.ui.View):
    def __init__(self, author_id, selector: discord.ui.Select, **kwargs):
        self.author_id = author_id
        self.custom_id = None
        super().__init__(timeout=30.0)

        self.add_item(selector(**kwargs))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "Sorry, you can't use this interaction as it is not started by you.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if hasattr(self, "message"):
            await self.message.delete()


class ChannelSelector(discord.ui.Select):
    def __init__(self, placeholder: str, channels: List[Union[discord.TextChannel, discord.VoiceChannel]]):

        _options = []
        for channel in channels:
            _options.append(
                discord.SelectOption(
                    label=channel.name,
                    value=channel.id,
                    description=f"{channel.name} ({channel.id})",
                    emoji=TextChannel if isinstance(channel, discord.TextChannel) else VoiceChannel,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = interaction.data["values"][0]
        self.view.stop()


class CustomSelector(discord.ui.Select):
    def __init__(self, placeholder: str, options: List[discord.SelectOption]):
        super().__init__(placeholder=placeholder, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = interaction.data["values"][0]
        self.view.stop()
