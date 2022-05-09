from __future__ import annotations

import discord

from utils import integer_input

from ...views.base import Context, EsportsBaseView


class NextButton(discord.ui.Button):
    view: "EsportsBaseView"

    def __init__(self):
        super().__init__(emoji="<:double_right:878668437193359392>")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        self.view.current_page += 1
        await self.view.refresh_view()


class PrevButton(discord.ui.Button):
    view: "EsportsBaseView"

    def __init__(self):
        super().__init__(emoji="<:double_left:878668594530099220>")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        self.view.current_page -= 1
        await self.view.refresh_view()


class SkipToButton(discord.ui.Button):
    view: "EsportsBaseView"

    def __init__(self, ctx: Context):
        super().__init__(label="Skip to page ...")
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple(
            "Please enter the page number you want to skip to. (`1` to `{}`)".format(len(self.view.records))
        )
        _page = await integer_input(self.ctx, timeout=30, delete_after=True, limits=(1, len(self.view.records)))
        await self.ctx.safe_delete(m)

        self.view.current_page = _page

        await self.view.refresh_view()


class StopButton(discord.ui.Button):
    view: "EsportsBaseView"

    def __init__(self):
        super().__init__(emoji="⏹️")

    async def callback(self, interaction: discord.Interaction):

        await self.view.on_timeout()
