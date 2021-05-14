from discord.ext import commands
from core import Cog


class ScrimError(commands.CommandError):
    pass


class SMError(Cog):
    def __init__(self, bot):
        self.bot = bot

    ...
