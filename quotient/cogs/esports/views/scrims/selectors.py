import discord
from lib import keycap_digit
from models import Day


class WeekDaysSelector(discord.ui.Select):
    def __init__(self, placeholder="Select the days for registrations", max=7):
        _o = []
        for idx, day in enumerate(Day, start=1):
            _o.append(discord.SelectOption(label=day.name.title(), value=day.value, emoji=keycap_digit(idx)))

        super().__init__(placeholder=placeholder, max_values=max, options=_o)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        self.view.selected_days = self.values
