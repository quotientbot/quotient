from __future__ import annotations

import discord

from models import Tourney

from ...views.base import EsportsBaseView


class TourneyView(EsportsBaseView):
    record: Tourney

    def __init__(self, ctx, **kwargs):
        super().__init__(ctx, **kwargs)


class TourneyButton(discord.ui.Button):
    view: TourneyView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
