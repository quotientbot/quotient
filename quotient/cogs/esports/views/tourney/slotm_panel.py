import os

import discord
from models import Tourney


class TourneySlotmPublicPanel(discord.ui.View):
    def __init__(self, tourney: Tourney):
        super().__init__(timeout=None)
        self.tourney = tourney
        self.bot = tourney.bot

    def initial_embed(self) -> discord.Embed:
        embed = discord.Embed(
            color=self.bot.color,
            description=(
                f"**[Tourney Slot Manager]({self.bot.config('SUPPORT_SERVER_LINK')})** ─ {self.tourney}\n\n"
                "• Click `Cancel My Slot` below to cancel your slot.\n"
                "• Click `My Slots` to get info about all your slots.\n"
                "• Click `Change Team Name` if you want to update your team's name.\n\n"
                "*Note that slot cancel is irreversible.*"
            ),
        )
        return embed
