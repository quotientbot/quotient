from __future__ import annotations

from typing import List

from core import QuotientView, Context
import discord

from utils import emote


class EsportsPaginator(QuotientView):
    """
    A pretty cool paginator + editor view
    """

    def __init__(self, ctx: Context, *, cur_page=1, pages: List[discord.Embed]):
        super().__init__(ctx, timeout=90)

        self.ctx = ctx
        self.pages = pages
        self.cur_page = cur_page
        self.total_pages = len(self.pages)

        if self.total_pages > 1:
            self.add_item(NextButton())

        self.add_item(StopButton())

        if self.cur_page > 1:
            self.add_item(PrevButton())


class NextButton(discord.ui.Button):
    view: "EsportsPaginator"

    def __init__(self):
        super().__init__(emoji=emote.pnext)

    async def callback(self, interaction: discord.Interaction):
        ...


class PrevButton(discord.ui.Button):
    view: "EsportsPaginator"

    def __init__(self):
        super().__init__(emoji=emote.pprevious)

    async def callback(self, interaction: discord.Interaction):
        ...


class StopButton(discord.ui.Button):
    view: "EsportsPaginator"

    def __init__(self):
        super().__init__(emoji=emote.pstop)

    async def callback(self, interaction: discord.Interaction):
        ...
