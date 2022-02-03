from __future__ import annotations

from ...views.base import EsportsBaseView
import discord


class NextButton(discord.ui.Button):
    view: "EsportsBaseView"

    def __init__(self):
        super().__init__(emoji="<:double_right:878668437193359392>")

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page += 1
        await self.view.refresh_view()


class PrevButton(discord.ui.Button):
    view: "EsportsBaseView"

    def __init__(self):
        super().__init__(emoji="<:double_left:878668594530099220>")

    async def callback(self, interaction: discord.Interaction):
        self.view.current_page -= 1
        await self.view.refresh_view()
