from __future__ import annotations

import typing as T

import discord

from core import QuotientView
from models import TMSlot, Tourney
from utils import emote


class TourneySelector(discord.ui.Select):
    view: QuotientView

    def __init__(self, placeholder: str, tourneys: T.List[Tourney]):

        _options = []
        for tourney in tourneys:
            _options.append(
                discord.SelectOption(
                    label=f"{getattr(tourney.registration_channel,'name','channel-deleted')} - (ID:{tourney.id})",
                    emoji=emote.TextChannel,
                    value=tourney.id,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.custom_id = self.values[0]

        self.view.stop()


class TourneySlotSelec(discord.ui.Select):
    view: QuotientView

    def __init__(self, slots: T.List[TMSlot], placeholder: str = "Select a slot to cancel"):
        _options = []

        for slot in slots:
            _options.append(
                discord.SelectOption(
                    emoji=emote.TextChannel,
                    label=f"Slot {slot.num} - {slot.team_name}",
                    description=f"#{getattr(slot.tourney.registration_channel,'name','channel-deleted')} - (ID:{slot.tourney.id})",
                    value=f"{slot.id}:{slot.tourney.id}",
                )
            )

        super().__init__(options=_options, placeholder=placeholder, max_values=len(_options))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()
        self.view.custom_id  = interaction.data["values"]
