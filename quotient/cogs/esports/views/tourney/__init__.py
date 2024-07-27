import discord
from core import QuoView
from discord.ext import commands
from models import Tourney


class TourneyView(QuoView):
    record: Tourney

    def __init__(self, ctx: commands.Context, timeout: int = 60):
        self.ctx = ctx

        super().__init__(ctx, timeout=timeout)

    async def refresh_view(self): ...


class TourneyBtn(discord.ui.Button):
    view: TourneyView

    def __init__(self, ctx: commands.Context, emoji: str = None, **kwargs):
        super().__init__(emoji=emoji, **kwargs)

        self.ctx = ctx
