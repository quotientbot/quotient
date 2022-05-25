from __future__ import annotations

import discord

from models import Scrim

from ...views.base import EsportsBaseView

__all__ = ("ScrimsView", "ScrimsButton")


class ScrimsView(EsportsBaseView):
    record: Scrim
    scrim:Scrim

    def __init__(self, ctx, **kwargs):
        super().__init__(ctx, **kwargs)


class ScrimsButton(discord.ui.Button):
    view: ScrimsView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
