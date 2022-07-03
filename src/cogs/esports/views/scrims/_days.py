from __future__ import annotations

import discord

from constants import Day
from utils import keycap_digit

__all__ = ("WeekDays",)


class WeekDays(discord.ui.Select):
    def __init__(self, placeholder="Select the weekdays for registrations", max=7):
        _o = []
        for idx, day in enumerate(Day, start=1):
            _o.append(discord.SelectOption(label=day.name.title(), value=day.name, emoji=keycap_digit(idx)))

        super().__init__(placeholder=placeholder, max_values=max, options=_o)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        self.view.custom_id = [Day(_) for _ in self.values]
