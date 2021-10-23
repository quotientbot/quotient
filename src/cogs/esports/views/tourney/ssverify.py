from __future__ import annotations

from ...views.base import EsportsBaseView
from core import Context
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core import Quotient

from utils import regional_indicator as ri, emote
from models import SSVerify
import discord


class SsVerifyView(EsportsBaseView):
    def __init__(self, ctx: Context, model: SSVerify):
        super().__init__(ctx, timeout=30, title="Screenshot-Moderator")

        self.model = model
        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    def initial_embed(model: SSVerify) -> discord.Embed:
        _e = discord.Embed(color=0x00FFB3, title="Screenshot-Mod Editor")

        return _e

    async def __update_model(self, **kwargs):
        await SSVerify.filter(pk=self.model.id).update(**kwargs)
        await self.__refresh_view()

    async def __refresh_view(self):
        await self.model.refresh_from_db()
        embed = self.initial_message(self.model)
        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(emoji=ri("A"), custom_id="ssverify_channel")
    async def set_channel(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("B"), custom_id="ssverify_role")
    async def set_role(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("C"), custom_id="ssverify_ss")
    async def set_required_ss(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("D"), custom_id="ssverify_name")
    async def set_name(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("E"), custom_id="ssverify_link")
    async def set_link(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("F"), custom_id="ssverify_logo")
    async def set_logo(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("G"), custom_id="ssverify_type")
    async def set_type(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("H"), custom_id="ssverify_delete_after")
    async def set_delete_after(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=ri("I"), custom_id="ssverify_message")
    async def set_message(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=emote.trash, custom_id="ssverify_delete")
    async def delete_ssverify(self, button: discord.ui.Button, interaction: discord.Interaction):
        ...
