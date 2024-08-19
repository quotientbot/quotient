import discord
from core import QuoView
from discord.ext import commands

from quotient.models import SSverify


class SsVerifyView(QuoView):
    record: SSverify

    def __init__(self, ctx: commands.Context, timeout: int = 60):
        self.ctx = ctx

        super().__init__(ctx, timeout=timeout)

    async def refresh_view(self): ...


class SsVerifyBtn(discord.ui.Button):
    view: SsVerifyView

    def __init__(self, ctx: commands.Context, emoji: str = None, **kwargs):
        super().__init__(emoji=emoji, **kwargs)

        self.ctx = ctx
