import discord
from discord.ext import commands
from models import ScrimsSlotManager

from .. import ScrimsView


class EditSlotmPanel(ScrimsView):
    def __init__(self, ctx: commands.Context, record: ScrimsSlotManager):
        super().__init__(ctx, timeout=100)
        self.record = record

    async def initial_msg(self) -> discord.Embed: ...

    async def refresh_view(self): ...
