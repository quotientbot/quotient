from models import Guild


class CacheManager:
    def __init__(self):
        self.prefixes: dict[int, str] = {}

    async def populate_internal_cache(self):
        async for guild in Guild.all():
            self.prefixes[guild.pk] = guild.prefix
