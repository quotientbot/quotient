from __future__ import annotations

import discord
from typing import Optional

from ._editor import TourneyEditor


class TourneyButton(discord.ui.Button):
    view: Optional[TourneyEditor]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
