from models import Tourney

from constants import EsportsRole



def tourney_work_role(tourney: Tourney, _type: EsportsRole):

    if _type == EsportsRole.ping:
        role = tourney.ping_role

    elif _type == EsportsRole.open:
        role = tourney.open_role

    if not role:
        return None

    if role == tourney.guild.default_role:
        return "@everyone"

    return getattr(role, "mention", "role-deleted")
