from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Context

from ...views.base import EsportsBaseView
from models import SSVerify

from utils import emote
from ._wiz import SetupWizard
from ._edit import SSmodEditor
import discord


class SsmodMainView(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=90, title="Screenshots Manager")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    async def initial_message(self):
        records = await SSVerify.filter(guild_id=self.ctx.guild.id).order_by("id")
        if not records:
            self.children[-2].disabled = True

        _to_show = [f"`{idx}.` {_.__str__()}" for idx, _ in enumerate(records, start=1)]

        _sm = "\n".join(_to_show) if _to_show else "```Click Setup button for new ssverify.```"

        _e = discord.Embed(color=0x00FFB3, title=f"Advanced Screenshots Manager", url=self.ctx.config.SERVER_LINK)
        _e.set_thumbnail(url=self.bot.user.display_avatar.url)
        _e.description = _sm
        _e.set_footer(text="When in doubt, press '?' :)", icon_url=getattr(self.ctx.author, "url", discord.Embed.Empty))
        return _e

    @discord.ui.button(label="Setup ssverify", custom_id="setup_ssverify_button", emoji=emote.add)
    async def setup_ssverify_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.ctx.is_premium_guild():
            if await SSVerify.filter(guild_id=self.ctx.guild.id).exists():
                return await self.ctx.premium_mango("You need Quotient Premium to setup more than 1 ssverify.")

        view = SetupWizard(self.ctx)
        _e = view.initial_message()
        view.message = await interaction.followup.send(embed=_e, view=view)

    @discord.ui.button(label="Change Settings", custom_id="edit_ssmod_config", emoji="⚒️")
    async def edit_ssmod_config(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        records = await SSVerify.filter(guild_id=self.ctx.guild.id).order_by("id")
        _view = SSmodEditor(self.ctx, records)
        await _view._add_buttons(self.ctx)
        _view.message = await interaction.followup.send(embed=await _view.initial_embed(records[0]), view=_view)

    @discord.ui.button(emoji="❔", custom_id="info_ssmod_button")
    async def stop_ssmod_button(self, button: discord.Button, interaction: discord.Interaction):
        _e = discord.Embed(color=0x00FFB3, title="Screenshots Manager FAQ", url=self.ctx.config.SERVER_LINK)
        _e.description = (
            "**How to setup Quotient ssverification?**\n"
            "> Click the `Setup ssverify` button to set up ssverify.\n\n"
            "**What is Custom Filter?**\n"
            "> Custom Filter allows you to set ssverification for any app or for any type of ss.\n\n"
            "**My question isn't listed here. What should I do?**\n"
            "> You can talk to us directly in the support server: {0}".format(self.ctx.config.SERVER_LINK)
        )
        return await interaction.response.send_message(embed=_e, ephemeral=True)
