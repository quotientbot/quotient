from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Context

from ...views.base import EsportsBaseView

import discord


class SsmodMainView(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=90, title="Screenshots Manager")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    async def initial_message(self):
        ...

    @discord.ui.button(label="Setup ssverify", custom_id="setup_ssverify_button")
    async def setup_ssverify_button(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Edit Config", custom_id="edit_ssmod_config")
    async def edit_ssmod_config(self, button: discord.Button, interaction: discord.Interaction):
        ...
