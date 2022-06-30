from __future__ import annotations

import discord

from models import Scrim

from ...views.base import EsportsBaseView

__all__ = ("ScrimsView", "ScrimsButton")


class ScrimsView(EsportsBaseView):
    record: Scrim
    # scrim:Scrim

    def __init__(self, ctx, **kwargs):
        super().__init__(ctx, **kwargs)

    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        print(error)


class ScrimsButton(discord.ui.Button):
    view: ScrimsView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
