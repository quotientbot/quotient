import discord

__all__ = ("MatchTimeEditor",)


class MatchTimeEditor(discord.ui.Button):
    def __init__(self, guild: discord.Guild):
        self.guild = guild

        super().__init__(label="Edit Match Time", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        ...
