from __future__ import annotations

import discord

from ...views.base import EsportsBaseView
from models import Tourney


class TourneyView(EsportsBaseView):
    record: Tourney

    def __init__(self, ctx, **kwargs):
        super().__init__(ctx, **kwargs)


class TourneyButton(discord.ui.Button):
    view: TourneyView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
