from core import Cog
from discord.ext import ipc


class IpcRoutes(Cog):
    def __init__(self, bot):
        self.bot = bot

    @ipc.server.route()
    async def get_member_count(self, data):
        guild = self.bot.get_guild(data.guild_id)
        return guild.member_count

    @ipc.server.route()
    async def create_scrim(self, payload):
        return dict()
