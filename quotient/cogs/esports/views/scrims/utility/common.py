from aiocache import cached

from quotient.models import Scrim


@cached(ttl=10)
async def get_scrim_position(scrim_id: int, guild_id: int) -> tuple[str, str]:
    """
    returns the position of scrim in all scrims of a server
    example: (1,10)
    """
    scrims = await Scrim.filter(guild_id=guild_id).order_by("reg_start_time")
    return str(scrims.index(next(s for s in scrims if s.pk == scrim_id)) + 1), len(scrims).__str__()
