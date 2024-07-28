from typing import Any

import discord
from discord.ext import commands

from quotient.models import Scrim

from . import ScrimsBtn, ScrimsView
from .utility.buttons import DiscardChanges
from .utility.common import get_scrim_position
from .utility.paginator import NextScrim, PreviousScrim, SkipToScrim


class InstantToggleView(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx=ctx, timeout=100)
        self.ctx = ctx
        self.record = scrim

    async def initial_msg(self):

        self.clear_items()
        all_scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")
        if len(all_scrims) > 1:
            self.add_item(PreviousScrim(self.ctx))
            self.add_item(SkipToScrim(self.ctx))
            self.add_item(NextScrim(self.ctx))

        self.add_item(StartRegistration(self.ctx))
        self.add_item(StopRegistration(self.ctx))
        self.add_item(DiscardChanges(self.ctx, row=2, label="Main Menu"))

        embed = discord.Embed(color=self.bot.color)
        embed.description = "**Start / Stop scrim registration of {}**".format(self.record)

        embed.set_footer(
            text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.ctx.guild.id))}",
            icon_url=self.ctx.author.display_avatar.url,
        )

        return embed


class StartRegistration(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.green, label="Start Reg", row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not self.view.record.reg_ended_at and self.view.record.reg_started_at:
            return await interaction.followup.send(
                embed=self.view.bot.error_embed("Registration is already open. To restart, pls stop registration first."),
                ephemeral=True,
            )
        try:
            await self.view.record.fetch_related("reserved_slots")
            await self.view.record.start_registration()
        except Exception as e:
            return await interaction.followup.send(embed=self.view.bot.error_embed(e), ephemeral=True)

        else:
            await interaction.followup.send(
                embed=self.view.bot.success_embed(f"Registration started for {self.view.record}"), ephemeral=True
            )
            await self.view.record.refresh_from_db()


class StopRegistration(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.red, label="Stop Reg", row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not self.view.record.reg_started_at:
            return await interaction.followup.send(
                embed=self.view.bot.error_embed("Registration is already closed."),
                ephemeral=True,
            )

        try:
            await self.view.record.close_registration()
        except Exception as e:
            return await interaction.followup.send(embed=self.view.bot.error_embed(e), ephemeral=True)

        else:
            await self.view.record.refresh_from_db()
            await interaction.followup.send(
                embed=self.view.bot.success_embed(f"Registration stopped for {self.view.record}"), ephemeral=True
            )
