from __future__ import annotations

import typing as T
from ._base import ScrimsView
import discord

from models import Scrim

from core import Context
from utils import regional_indicator as ri

from core.embeds import EmbedBuilder
import config
from enum import Enum


class MsgType(Enum):
    open = "1"
    close = "2"
    countdown = "3"


class ScrimDesign(ScrimsView):
    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(ctx, timeout=60.0)

        self.scrim = scrim
        self.ctx = ctx

    @staticmethod
    def default_open_msg():
        return discord.Embed(
            color=config.COLOR,
            title="Registration is now open!",
            description=f"📣 **`<<mentions>>`** mentions required.\n"
            f"📣 Total slots: **`<<slots>>`** [`<<reserved>>` slots reserved]",
        )

    @property
    def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3)
        _e.description = (
            f"[**Scrims - Design Settings - {self.scrim}**]({self.ctx.config.SERVER_LINK})\n"
            "What do you want to design today?\n\n"
            f"{ri('a')} - Registration Open Message\n"
            f"{ri('b')} - Registration Close Message\n"
            f"{ri('c')} - Registratipn Open Countdown\n"
            f"{ri('d')} - Slotlist Design\n"
        )
        return _e

    @discord.ui.button(emoji=ri("a"))
    async def reg_open_message(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

        if len(self.scrim.open_message) <= 1:
            _e = ScrimDesign.default_open_msg()

        else:
            _e = discord.Embed.from_dict(self.scrim.open_message)

        self.stop()
        await self.message.delete()
        await self.ctx.simple("Edit this message to set new registration open message.", 4)
        _v = EmbedBuilder(
            self.ctx,
            items=[
                SaveMessageBtn(self.ctx, self.scrim, MsgType.open),
                BackBtn(self.ctx, self.scrim),
                SetDefault(self.ctx, self.scrim, MsgType.open),
            ],
        )

        await _v.rendor(embed=_e)

    @discord.ui.button(emoji=ri("b"))
    async def reg_clse_message(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(emoji=ri("c"))
    async def pre_reg_msg(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

    @discord.ui.button(emoji=ri("d"))
    async def slotlist_design(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()


class SaveMessageBtn(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim, _type: MsgType):
        super().__init__(style=discord.ButtonStyle.green, label="Save this design")
        self.scrim = scrim

        self.ctx = ctx
        self._type = _type

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class BackBtn(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(style=discord.ButtonStyle.red, label="Exit")
        self.ctx = ctx
        self.scrim = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = await self.ctx.prompt("All unsaved changes will be lost forever. Do you still want to continue?")
        if not prompt:
            return await self.ctx.simple("OK. Not Exiting.", 4)

        self.view.stop()
        v = ScrimDesign(self.ctx, self.scrim)
        v.message = await self.view.message.edit(embed=v.initial_embed, view=v)


class SetDefault(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim, _type: MsgType):
        super().__init__(style=discord.ButtonStyle.blurple, label="Reset to default")
        self._type = _type
        self.scrim = scrim
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = await self.ctx.prompt("All changes will be lost. Do you still want to continue?")
        if not prompt:
            return await self.ctx.simple("OK, not reseting.", 3)

        if self._type == MsgType.open:
            self.view.embed = ScrimDesign.default_open_msg()

        elif self._type == MsgType.close:
            self.view.embed = ScrimDesign.default_close_msg()

        else:
            self.view.embed = ScrimDesign.default_countdown_msg()

        self.view.content = ""
        await self.view.refresh_view()
        await self.ctx.success("Message set to default. Click `Save` to save this design.", 4)
