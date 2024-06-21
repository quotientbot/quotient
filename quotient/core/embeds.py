import discord
from discord.ext import commands

from .views import QuoView


class EmbedBuilder(QuoView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)
