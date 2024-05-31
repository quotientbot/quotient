from models import AutoPurge, Guild


class CacheManager:
    def __init__(self):
        self.prefixes: dict[int, str] = {}
        self.autopurge_channel_ids: set[int] = set()

    async def populate_internal_cache(self):
        async for guild in Guild.all():
            self.prefixes[guild.pk] = guild.prefix

        async for record in AutoPurge.all():
            self.autopurge_channel_ids.add(record.channel_id)
