from .errors import ErrorHandler
from .guilds import GuildEvents
from .startup import StartupEvents


async def setup(bot):
    await bot.add_cog(StartupEvents(bot))
    await bot.add_cog(GuildEvents(bot))
    await bot.add_cog(ErrorHandler(bot))
