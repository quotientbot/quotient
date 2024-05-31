from .startup import StartupEvents


async def setup(bot):
    await bot.add_cog(StartupEvents(bot))
