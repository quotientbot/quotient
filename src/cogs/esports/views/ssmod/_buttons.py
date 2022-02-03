from __future__ import annotations

from core import Context

from utils import keycap_digit as kd, inputs, truncate_string, BaseSelector
import discord
from ._type import SStypeSelector

from constants import SSType


class SetChannel(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(1))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Mention the channel you want to use for ssverification.")
        channel = await inputs.channel_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.channel_id = channel.id

        await self.view.refresh_view()


class SetRole(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(2))
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Mention the role you want to give for ssverification.")
        role = await inputs.role_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.role_id = role.id

        await self.view.refresh_view()


class RequiredSS(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(3))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("How many screenshots do you need me to verify?")
        _ss = await inputs.integer_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.required_ss = _ss

        await self.view.refresh_view()


class ScreenshotType(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(4))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _v = BaseSelector(self.ctx.author.id, SStypeSelector)
        _m = await self.ctx.simple("What type of screenshots do you want to verify?", view=_v)
        await _v.wait()
        await _m.delete()
        if _v.custom_id:
            self.view.record.ss_type = SSType(_v.custom_id)

            if _v.custom_id == "custom":

                _m = await self.ctx.simple(
                    "What name do want to give this filter?\n\n" "Enter any name relevant to what you want to verify.\n"
                )
                _name = await inputs.string_input(self.ctx, delete_after=True)
                await self.ctx.safe_delete(_m)
                _name = truncate_string(_name, max_length=50)

                _m = await self.ctx.simple(
                    "What words might appear in the screenshot? Maybe like name of the game/app or "
                    "anything that you believe to be common in the screenshots.\n\n"
                    "*Separate with comma `,`*"
                )
                _keys = await inputs.string_input(self.ctx, delete_after=True)
                await self.ctx.safe_delete(_m)

                _keys = _keys.split(",")
                self.view.record.keywords = [_name, *[truncate_string(i, 50).strip() for i in _keys]]

                await self.ctx.success("Successfully set custom filter.", 3)

        await self.view.refresh_view()


class PageName(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(5))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Enter the exact name of your page/channel.")
        _name = await inputs.string_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.channel_name = truncate_string(_name, 30)
        await self.view.refresh_view()


class PageLink(discord.ui.Button):
    def __init__(self, ctx: Context):
        super().__init__(emoji=kd(6))

        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        _m = await self.ctx.simple("Enter the direct link to your page/channel.")
        _name = await inputs.string_input(self.ctx, delete_after=True)

        await self.ctx.safe_delete(_m)
        self.view.record.channel_link = truncate_string(_name, 130)
        await self.view.refresh_view()


class DiscardButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Discard", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        return await self.view.on_timeout()


class SaveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Save & Setup", style=discord.ButtonStyle.green, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        ...
