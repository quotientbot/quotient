from __future__ import annotations

import discord
from models import Tourney
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
