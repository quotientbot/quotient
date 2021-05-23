from core import Cog, Quotient, Context
import discord

__all__ = ("ModEvents",)


class ModEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Mute them if they were muted
        """
        pass
