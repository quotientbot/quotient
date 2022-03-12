from __future__ import annotations
import typing as T

from ..base import EsportsBaseView
from core import Context


class GroupPages(EsportsBaseView):
    def __init__(self, ctx: Context, *, ping_role=True, **kwargs):
        super().__init__(ctx)

        self.ping_role = ping_role
        self.current_page = 1

    async def render(self):
        ...