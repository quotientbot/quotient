from __future__ import annotations

import discord

from core import Context
from core.embeds import EmbedBuilder
from models import Scrim

DEFAULT_MSG = Scrim.default_slotlist_format()

__all__ = ("show_slotlist_formatter",)


async def show_slotlist_formatter(ctx: Context, scrim: Scrim, view_msg: discord.Message):
    await scrim.refresh_from_db()

    embed = discord.Embed(color=ctx.bot.color, title="Click me to Get Help", url=ctx.config.SERVER_LINK)
    embed.description = (
        f"\n*You are editing slotlist design for {scrim}*\n\n"
        "**__Keywords you can use in design:__**\n"
        "`<<slots>>` - Slot number and team names (**Most Important**)\n"
        "`<<name>>` -  Name of the scrim\n"
        "`<<open_time>>` - Next day's registration open time.\n"
        "`<<time_taken>>` - Time taken in registration.\n"
    )

    await view_msg.edit(embed=embed, content="", view=None)

    if len(scrim.slotlist_format) <= 1:
        embed = DEFAULT_MSG
    else:
        embed = discord.Embed.from_dict(scrim.slotlist_format)

    _v = EmbedBuilder(
        ctx,
        items=[
            SaveBtn(ctx, scrim, view_msg),
            BackBtn(ctx, scrim, view_msg),
            SetDefault(ctx, scrim),
        ],
    )

    await _v.rendor(embed=embed)


class SaveBtn(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim, msg: discord.Message = None):
        super().__init__(style=discord.ButtonStyle.green, label="Save this design")

        self.ctx = ctx
        self.scrim = scrim
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.ctx.simple(f"Saving Changes...", 2)

        await self.scrim.make_changes(slotlist_format=self.view.formatted)
        await self.scrim.confirm_all_scrims(self.ctx, slotlist_format=self.view.formatted)

        await self.ctx.success(f"Saved your new design!", 2)
        self.view.stop()

        if self.msg:
            await self.ctx.safe_delete(self.msg)

        from .main import ScrimsMain

        v = ScrimsMain(self.ctx)
        v.message = await self.view.message.edit(content="", embed=await v.initial_embed(), view=v)


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

        from .main import ScrimsMain

        v = ScrimsMain(self.ctx)
        v.message = await self.view.message.edit(content="", embed=await v.initial_embed(), view=v)


class SetDefault(discord.ui.Button):
    view: EmbedBuilder

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(style=discord.ButtonStyle.blurple, label="Reset to default")

        self.scrim = scrim
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = await self.ctx.prompt("All changes will be lost. Do you still want to continue?")
        if not prompt:
            return await self.ctx.simple("OK, not reseting.", 3)

        self.view.embed = DEFAULT_MSG

        self.view.content = ""
        await self.view.refresh_view()
        await self.ctx.success("Slotlist design set to default. Click `Save` to save this design.", 4)
