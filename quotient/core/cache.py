from quotient.models import AutoPurge, Guild, Scrim, TagCheck, Tourney


class CacheManager:
    def __init__(self):
        self.prefixes: dict[int, str] = {}
        self.autopurge_channel_ids: set[int] = set()
        self.scrim_channel_ids: set[int] = set()
        self.tagcheck_channel_ids: set[int] = set()
        self.tourney_channel_ids: set[int] = set()

    async def populate_internal_cache(self):
        async for guild in Guild.all():
            self.prefixes[guild.pk] = guild.prefix

        async for record in AutoPurge.all():
            self.autopurge_channel_ids.add(record.channel_id)

        async for scrim in Scrim.all():
            self.scrim_channel_ids.add(scrim.registration_channel_id)

        async for tagcheck in TagCheck.all():
            self.tagcheck_channel_ids.add(tagcheck.channel_id)

        async for tourney in Tourney.all():
            self.tourney_channel_ids.add(tourney.registration_channel_id)
