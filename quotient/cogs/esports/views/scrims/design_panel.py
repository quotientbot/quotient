from enum import Enum

import discord
from core import EmbedBuilder
from discord.ext import commands
from lib import EXIT, regional_indicator, send_simple_embed
from models import RegCloseMsgVar, RegOpenMsgVar, Scrim, SlotlistMsgVar
from models.esports.utility import (
    default_reg_close_msg,
    default_reg_open_msg,
    default_slotlist_msg,
)

from . import ScrimsBtn, ScrimsView
from .utility.buttons import DiscardChanges
from .utility.common import get_scrim_position
from .utility.paginator import NextScrim, PreviousScrim, SkipToScrim


class RegMsgType(Enum):
    OPEN = "open"
    CLOSE = "close"
    SLOTLIST = "slotlist"


class ScrimsDesignPanel(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx, timeout=100)
        self.record = scrim

    async def initial_msg(self) -> discord.Embed:
        scrims = await Scrim.filter(guild_id=self.record.guild_id).order_by("reg_start_time")

        self.clear_items()

        self.add_item(EditOpenMsg(self.ctx))
        self.add_item(EditCloseMsg(self.ctx))
        self.add_item(EditSlotlistMsg(self.ctx))

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx, row=2))
            self.add_item(SkipToScrim(self.ctx, row=2))
            self.add_item(NextScrim(self.ctx, row=2))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT, row=2))

        e = discord.Embed(color=0x00FFB3)
        e.description = f"**{self.record} - Design Settings**\n"

        e.description += (
            "What do you want to design today?\n\n"
            f"{regional_indicator('a')} - Registration Open Message\n"
            f"{regional_indicator('b')} - Registration Close Message\n"
            f"{regional_indicator('c')} - Slotlist Design\n"
        )

        e.set_footer(text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.record.guild_id))}")
        return e

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()


class EditOpenMsg(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, emoji=regional_indicator("A"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        e = discord.Embed(color=self.view.bot.color, title="Edit Registration Open Message")
        e.description = (
            f"*You are editing registration open message for {self.view.record}.*\n\n**__Keywords you can use in design:__**\n"
        )

        for var in RegOpenMsgVar:
            e.description += f"`<<{var.name.lower()}>>` - {var.value}\n"

        await self.view.message.edit(embed=e, view=None)

        v = EmbedBuilder(
            self.ctx,
            embed=discord.Embed.from_dict(self.view.record.open_msg_design),
            extra_items=[
                SaveDesign(self.ctx, self.view.record, RegMsgType.OPEN, self.view.message),
                ResetDefault(self.ctx, self.view.record, RegMsgType.OPEN),
                BackBtn(self.ctx, self.view.record, self.view.message),
            ],
        )
        v.message = await self.ctx.send(embed=v.embed, view=v)


class EditCloseMsg(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, emoji=regional_indicator("B"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        e = discord.Embed(color=self.view.bot.color, title="Edit Registration Close Message")
        e.description = (
            f"*You are editing registration close message for {self.view.record}.*\n\n**__Keywords you can use in design:__**\n"
        )

        for var in RegCloseMsgVar:
            e.description += f"`<<{var.name.lower()}>>` - {var.value}\n"

        await self.view.message.edit(embed=e, view=None)

        v = EmbedBuilder(
            self.ctx,
            embed=discord.Embed.from_dict(self.view.record.close_msg_design),
            extra_items=[
                SaveDesign(self.ctx, self.view.record, RegMsgType.CLOSE, self.view.message),
                ResetDefault(self.ctx, self.view.record, RegMsgType.CLOSE),
                BackBtn(self.ctx, self.view.record, self.view.message),
            ],
        )
        v.message = await self.ctx.send(embed=v.embed, view=v)


class EditSlotlistMsg(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, emoji=regional_indicator("C"))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        e = discord.Embed(color=self.view.bot.color, title="Edit Slotlist Design")
        e.description = f"*You are editing slotlist design for {self.view.record}.*\n\n**__Keywords you can use in design:__**\n"

        for var in SlotlistMsgVar:
            e.description += f"`<<{var.name.lower()}>>` - {var.value}\n"

        await self.view.message.edit(embed=e, view=None)

        v = EmbedBuilder(
            self.ctx,
            embed=discord.Embed.from_dict(self.view.record.slotlist_msg_design),
            extra_items=[
                SaveDesign(self.ctx, self.view.record, RegMsgType.SLOTLIST, self.view.message),
                ResetDefault(self.ctx, self.view.record, RegMsgType.SLOTLIST),
                BackBtn(self.ctx, self.view.record, self.view.message),
            ],
        )
        v.message = await self.ctx.send(embed=v.embed, view=v)


class SaveDesign(ScrimsBtn):
    view: EmbedBuilder

    def __init__(self, ctx: commands.Context, scrim: Scrim, msg_type: RegMsgType, msg: discord.Message):
        super().__init__(ctx, style=discord.ButtonStyle.green, label="Save Design", emoji="💾")

        self.scrim = scrim
        self.msg_type = msg_type
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        if self.msg_type == RegMsgType.OPEN:
            self.scrim.open_msg_design = self.view.embed.to_dict()
            await self.scrim.save(update_fields=["open_msg_design"])
            await self.scrim.confirm_change_for_all_scrims(interaction, open_msg_design=self.scrim.open_msg_design)

        elif self.msg_type == RegMsgType.CLOSE:
            self.scrim.close_msg_design = self.view.embed.to_dict()
            await self.scrim.save(update_fields=["close_msg_design"])
            await self.scrim.confirm_change_for_all_scrims(interaction, close_msg_design=self.scrim.close_msg_design)

        elif self.msg_type == RegMsgType.SLOTLIST:
            self.scrim.slotlist_msg_design = self.view.embed.to_dict()
            await self.scrim.save(update_fields=["slotlist_msg_design"])
            await self.scrim.confirm_change_for_all_scrims(interaction, slotlist_msg_design=self.scrim.slotlist_msg_design)

        await interaction.followup.send(embed=self.view.bot.success_embed("Design saved successfully."), ephemeral=True)
        self.view.stop()
        await self.msg.delete(delay=0)

        v = ScrimsDesignPanel(self.ctx, self.scrim)
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class BackBtn(ScrimsBtn):
    view: EmbedBuilder

    def __init__(self, ctx: commands.Context, scrim: Scrim, msg: discord.Message):
        super().__init__(ctx, style=discord.ButtonStyle.red, label="Back", emoji=EXIT)

        self.scrim = scrim
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        prompt = await self.view.bot.prompt(
            interaction, self.ctx.author, "All unsaved changes will be lost. Are you sure you want to go back?", ephemeral=True
        )
        if not prompt:
            return await interaction.followup.send(embed=self.view.bot.success_embed("Ok, Not exiting."), ephemeral=True)

        self.view.stop()

        await self.msg.delete(delay=0)
        v = ScrimsDesignPanel(self.ctx, self.scrim)
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class ResetDefault(ScrimsBtn):
    view: EmbedBuilder

    def __init__(self, ctx: commands.Context, scrim: Scrim, msg_type: RegMsgType):
        super().__init__(ctx, style=discord.ButtonStyle.red, label="Reset to Default", emoji="🔄")

        self.scrim = scrim
        self.msg_type = msg_type

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        prompt = await self.view.bot.prompt(
            interaction,
            self.ctx.author,
            "Are you sure you want to reset this design to default?",
            ephemeral=True,
        )

        if not prompt:
            return await interaction.followup.send(embed=self.view.bot.success_embed("Ok, Not resetting."), ephemeral=True)

        if self.msg_type == RegMsgType.OPEN:
            self.view.embed = default_reg_open_msg()
        elif self.msg_type == RegMsgType.CLOSE:
            self.view.embed = default_reg_close_msg()
        elif self.msg_type == RegMsgType.SLOTLIST:
            self.view.embed = default_slotlist_msg()

        await self.view.refresh_view()
        await send_simple_embed(interaction.channel, "Message set to default. Click `Save` to save this design.", 4)
