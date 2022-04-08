from __future__ import annotations
import typing as T
from core.Context import Context

import discord
from .views import QuotientView
from utils import keycap_digit as kd, string_input, truncate_string

_d = {
    "Content": 1,
    "Title": 2,
    "Description": 3,
    "Title URL": 4,
    "Large Image": 5,
    "Small Image (Thumbnail)": 6,
    "Footer Text": 7,
    "Footer Icon": 8,
    # "Add Field": 9,
}


class EmbedOptions(discord.ui.Select):
    def __init__(self, ctx: Context):
        self.ctx = ctx
        super().__init__(
            options=[discord.SelectOption(label=x, value=y, emoji=kd(idx)) for idx, (x, y) in enumerate(_d.items(), 1)]
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if (selected := _d[self.values[0]]) == 1:
            m = await self.ctx.simple("What message should be displayed above the embed? (Max `1000 chars`)", 60)
            self.content = truncate_string(await string_input(self.ctx, timeout=60, delete_after=True), 1000)
            await self.ctx.safe_delete(m)

        elif selected == 2:
            ...

        elif selected == 3:
            ...

        elif selected == 4:
            ...

        elif selected == 5:
            ...

        elif selected == 6:
            ...

        elif selected == 7:
            ...

        elif selected == 8:
            ...

        elif selected == 9:
            ...


class EmbedBuilder(QuotientView):
    def __init__(self, ctx: Context, message=None, content=None, embed=None):
        super().__init__(ctx, timeout=100)

        self.ctx = ctx

        self.message: discord.Message = message
        self.content = content or ""
        self.embed = embed or discord.Embed(color=self.bot.color)

        self.add_item(EmbedOptions(self.ctx))

    @property
    def fomatted(self):
        return {"content": self.content, "embed": self.embed.to_dict()}

    async def refresh_view(self):
        self.message = ...
