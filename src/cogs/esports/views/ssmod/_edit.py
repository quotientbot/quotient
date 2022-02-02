from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core import Quotient

from core import Context
from models import SSVerify

# from ...views.base import EsportsBaseView
from ...views.paginator import EsportsPaginator

import discord


class SSmodEditor(EsportsPaginator):
    def __init__(self, ctx: Context, pages: List[discord.Embed], records: List[SSVerify]):
        super().__init__(ctx, pages=pages)

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @discord.ui.button(label="this", custom_id="something")
    async def some_button(self, interaction: discord.Interaction, button: discord.Button):
        ...
