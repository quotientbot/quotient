import discord
from core import QuoView
from discord.ext import commands

from quotient.models import Scrim


class ScrimsView(QuoView):
    record: Scrim

    def __init__(self, ctx: commands.Context, timeout: int = 60):
        self.ctx = ctx

        super().__init__(ctx, timeout=timeout)

    async def refresh_view(self): ...


class ScrimsBtn(discord.ui.Button):
    view: ScrimsView

    def __init__(self, ctx: commands.Context, emoji: str = None, **kwargs):
        super().__init__(emoji=emoji, **kwargs)

        self.ctx = ctx
