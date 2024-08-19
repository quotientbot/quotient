from aiocache import cached

from quotient.models import SSverify


@cached(ttl=10)
async def get_ssverify_position(record_id: int, guild_id: int) -> tuple[str, str]:
    """
    returns the position of ssverify in all ssverify records of a server
    example: (1,10)
    """
    records = await SSverify.filter(guild_id=guild_id).order_by("id")
    return str(records.index(next(s for s in records if s.pk == record_id)) + 1), len(records).__str__()
