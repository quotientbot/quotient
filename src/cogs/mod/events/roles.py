from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from core import Cog


class RoleEvents(Cog):
    def __init__(self, bot: Quotient):
        self.bot = bot
