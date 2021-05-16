from discord.ext import commands
from core import Cog
import discord


class ScrimError(commands.CommandError):
    pass


class SMError(Cog):
    def __init__(self, bot):
        self.bot = bot

    def red_embed(self, description: str):
        embed = discord.Embed(color=discord.Color.red(), description=description)
        return embed

    @Cog.listener()
    async def on_scrim_registration_deny(self, message, type, scrim):
        logschan = scrim.logschan
            
