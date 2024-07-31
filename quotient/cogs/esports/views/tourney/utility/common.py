from aiocache import cached

from quotient.models import Tourney


@cached(ttl=10)
async def get_tourney_position(tourney_id: int, guild_id: int) -> tuple[str, str]:
    """
    returns the position of tourney in all tourneys of a server
    example: (1,10)
    """
    tourneys = await Tourney.filter(guild_id=guild_id).order_by("id")
    return str(tourneys.index(next(s for s in tourneys if s.pk == tourney_id)) + 1), len(tourneys).__str__()
