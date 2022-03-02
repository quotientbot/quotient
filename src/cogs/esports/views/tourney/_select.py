from __future__ import annotations

import discord
from models import Tourney, TMSlot
import typing as T


from utils import emote
from core import QuotientView


class TourneySelector(discord.ui.Select):
    view: QuotientView

    def __init__(self, placeholder: str, tourneys: T.List[Tourney]):

        _options = []
        for tourney in tourneys:
            _options.append(
                discord.SelectOption(
                    label=f"{getattr(tourney.registration_channel,'name','channel-deleted')} - (ID:{tourney.id})",
                    description=f"Click to {'PAUSE' if tourney.started_at else 'START'} the tourney registrations",
                    emoji=emote.TextChannel,
                    value=tourney.id,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
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
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0] if not self.max_values > 1 else interaction.data["values"]
