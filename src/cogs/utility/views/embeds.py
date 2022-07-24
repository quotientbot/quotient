from __future__ import annotations
from core.embeds import EmbedBuilder
import discord
from utils import emote
import typing as T

__all__ = ("EmbedSend", "EmbedCancel")


class EmbedSend(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, channel: discord.TextChannel):
        self.channel = channel
        super().__init__(label="Send to #{0}".format(channel.name), style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        try:
            m: T.Optional[discord.Message] = await self.channel.send(embed=self.view.embed)

        except Exception as e:
            await interaction.response.send_message(f"An error occured: {e}", ephemeral=True)

        else:
            await interaction.response.send_message(
                f"{emote.check} | Embed was sent to {self.channel.mention} ([Jump URL](<{m.jump_url}>))", ephemeral=True
            )
            await self.view.on_timeout()


class EmbedCancel(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        await interaction.response.send_message(f"{emote.xmark} | Embed sending cancelled.", ephemeral=True)
        await self.view.on_timeout()
