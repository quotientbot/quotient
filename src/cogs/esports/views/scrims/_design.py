from __future__ import annotations

import typing as T
from enum import Enum

import discord

import config
from core import Context
from core.embeds import EmbedBuilder
from models import Scrim
from utils import regional_indicator as ri

from ._cdn import ScrimsCDN
from ._base import ScrimsView


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

    @staticmethod
    def default_close_msg():
        return discord.Embed(color=config.COLOR, description="**Registration is now Closed!**")

    @staticmethod
    def default_countdown_msg():
        return discord.Embed(color=config.COLOR, description="*Registration is starting in* **`<<t>>` seconds.**")

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
        await self.scrim.refresh_from_db()

        if len(self.scrim.open_message) <= 1:
            _e = ScrimDesign.default_open_msg()

        else:
            _e = discord.Embed.from_dict(self.scrim.open_message)

        self.stop()

        embed = discord.Embed(color=self.bot.color, title="Click me to Get Help", url=config.SERVER_LINK)
        embed.description = (
            f"\n*You are editing registration open message for {self.scrim}*\n\n"
            "**__Keywords you can use in design:__**\n"
            "`<<mentions>>` - Number of mentions required\n"
            "`<<slots>>` - Total slots in this scrim\n"
            "`<<reserved>>` - Number of Reserved slots\n"
            "`<<slotlist>>` - Slotlist Channel mention.\n"
            "`<<mention_banned>>` -  Mention banned users.\n"
            "`<<mention_reserved>>` - Mention reserved slot owners.\n"
        )
        await self.message.edit(embed=embed, content="", view=None)

        _v = EmbedBuilder(
            self.ctx,
            items=[
                SaveMessageBtn(self.ctx, self.scrim, MsgType.open, self.message),
                BackBtn(self.ctx, self.scrim, self.message),
                SetDefault(self.ctx, self.scrim, MsgType.open),
            ],
        )

        await _v.rendor(embed=_e)

    @discord.ui.button(emoji=ri("b"))
    async def reg_clse_message(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()
        await self.scrim.refresh_from_db()

        if len(self.scrim.close_message) <= 1:
            _e = ScrimDesign.default_close_msg()

        else:
            _e = discord.Embed.from_dict(self.scrim.close_message)

        self.stop()
        embed = discord.Embed(color=self.bot.color, title="Click Me if you need Help", url=self.bot.config.SERVER_LINK)
        embed.description = (
            f"\n*You are editing registration close message for {self.scrim}*\n\n"
            "**__Keywords you can use in design:__**\n"
            "`<<slots>>` - Total slots in this scrim.\n"
            "`<<filled>>` - Number of slots filled during registration.\n"
            "`<<time_taken>>` - Time taken in registration.\n"
            "`<<open_time>>` - Next day's registration time."
        )
        await self.message.edit(embed=embed, content="", view=None)

        _v = EmbedBuilder(
            self.ctx,
            items=[
                SaveMessageBtn(self.ctx, self.scrim, MsgType.close, self.message),
                BackBtn(self.ctx, self.scrim, self.message),
                SetDefault(self.ctx, self.scrim, MsgType.close),
            ],
        )

        await _v.rendor(embed=_e)

    @discord.ui.button(emoji=ri("c"))
    async def pre_reg_msg(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()

        self.stop()
        v = ScrimsCDN(self.ctx, self.scrim)
        v.message = await self.message.edit(embed=v.initial_embed, view=v)

    @discord.ui.button(emoji=ri("d"))
    async def slotlist_design(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()
        await self.scrim.refresh_from_db()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Back")
    async def go_back(self, btn: discord.ui.Button, inter: discord.Interaction):
        await inter.response.defer()


class SaveMessageBtn(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim, _type: MsgType, msg: discord.Message = None):
        super().__init__(style=discord.ButtonStyle.green, label="Save this design")
        self.scrim = scrim

        self.ctx = ctx
        self.msg = msg
        self._type = _type

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.ctx.simple(f"Saving Changes...", 2)

        if self._type == MsgType.open:
            await self.scrim.make_changes(open_message=self.view.formatted)
            await self.scrim.confirm_all_scrims(self.ctx, open_message=self.view.formatted)

        elif self._type == MsgType.close:
            await self.scrim.make_changes(close_message=self.view.formatted)
            await self.scrim.confirm_all_scrims(self.ctx, close_message=self.view.formatted)

        elif self._type == MsgType.countdown:
            self.scrim.cdn["msg"] = self.view.formatted
            await self.scrim.make_changes(cdn=self.scrim.cdn)
            await self.scrim.confirm_all_scrims(self.ctx, cdn=self.scrim.cdn)

        await self.ctx.success(f"Saved!", 2)

        self.view.stop()

        if self.msg:
            await self.ctx.safe_delete(self.msg)

        v = ScrimDesign(self.ctx, self.scrim)
        v.message = await self.view.message.edit(embed=v.initial_embed, view=v)


class BackBtn(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim, msg: discord.Message = None):
        super().__init__(style=discord.ButtonStyle.red, label="Exit")
        self.ctx = ctx
        self.scrim = scrim

        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = await self.ctx.prompt("All unsaved changes will be lost forever. Do you still want to continue?")
        if not prompt:
            return await self.ctx.simple("OK. Not Exiting.", 4)

        self.view.stop()

        if self.msg:
            await self.ctx.safe_delete(self.msg)
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
