from __future__ import annotations

import discord

from ...views.base import EsportsBaseView
from models import Scrim

__all__ = ("ScrimsView", "ScrimsButton")


class ScrimsView(EsportsBaseView):
    record: Scrim

    def __init__(self, ctx, **kwargs):
        super().__init__(ctx, **kwargs)


class ScrimsButton(discord.ui.Button):
    view: ScrimsView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
