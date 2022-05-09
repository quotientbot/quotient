from __future__ import annotations

import discord

from constants import SSType
from utils import BaseSelector


class SStypeSelector(discord.ui.Select):
    view: BaseSelector

    def __init__(self):
        super().__init__(
            placeholder="Select the type of screenshots ... ",
            options=[
                discord.SelectOption(
                    label="Youtube",
                    emoji="<:youtube:938835185976344576>",
                    value=SSType.yt.value,
                    description="Youtube Channel Screenshots",
                ),
                discord.SelectOption(
                    label="Instagram",
                    emoji="<:instagram:938834438656249896>",
                    value=SSType.insta.value,
                    description="Instagram Screenshots (Premium only)",
                ),
                discord.SelectOption(
                    label="Rooter",
                    emoji="<:rooter:938834226483171418>",
                    value=SSType.rooter.value,
                    description="Rooter Screenshots (Premium only)",
                ),
                discord.SelectOption(
                    label="Loco",
                    emoji="<:loco:938834181088219146>",
                    value=SSType.loco.value,
                    description="Loco Screenshots (Premium only)",
                ),
                discord.SelectOption(
                    label="Any SS",
                    emoji="<:hehe:874303673981878272>",
                    value=SSType.anyss.value,
                    description="Verify any Image (Premium only)",
                ),
                discord.SelectOption(
                    label="Create Custom Filter",
                    emoji="<a:rooCoder:881404453415186502>",
                    value=SSType.custom.value,
                    description="For anything like app installation, any mobile app,etc.",
                ),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]
