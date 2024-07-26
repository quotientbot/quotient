from datetime import timedelta
from random import randint

import discord
from cogs.premium import SCRIMS_LIMIT, RequirePremiumView
from discord.ext import commands
from lib import INFO, send_error_embed, text_channel_input
from models import Guild, Scrim

from .. import ScrimsBtn
from .callbacks import (
    edit_match_start_time,
    edit_reactions,
    edit_reg_start_time,
    edit_registration_open_days,
    edit_required_mentions,
    edit_total_slots,
)


class SetRegChannel(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        channel = await text_channel_input(interaction, "Please mention the channel you want to set as the registration channel.")

        if not channel:
            return

        if await Scrim.filter(registration_channel_id=channel.id).exists():
            return await send_error_embed(interaction.channel, "That channel is already in use for another scrim.", 5)

        self.view.record.registration_channel_id = channel.id

        await self.view.refresh_view()


class SetMentions(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_required_mentions(self, interaction)


class SetTotalSlots(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_total_slots(self, interaction)


class SetRegStartTime(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        await edit_reg_start_time(self, interaction)


class SetMatchStartTime(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        await edit_match_start_time(self, interaction)


class SetRegOpenDays(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        await edit_registration_open_days(self, interaction)


class SetReactions(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        await edit_reactions(self, interaction)


class DiscardChanges(ScrimsBtn):
    def __init__(self, ctx: commands.Context, label="Back", row: int = None, **kwargs):
        super().__init__(ctx=ctx, style=discord.ButtonStyle.red, label=label, row=row, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from ..main_panel import ScrimsMainPanel

        self.view.stop()

        v = ScrimsMainPanel(self.ctx)
        v.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.view.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class SaveScrim(ScrimsBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.green, label="Save Scrim", emoji="📁", disabled=True)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await self.view.record.setup_logs()
        except Exception as e:
            return await interaction.followup.send(
                embed=self.view.bot.error_embed(f"An error occurred while creating scrim: {e}"),
                view=self.view.bot.contact_support_view(),
            )

        self.view.record.autoclean_channel_time = self.view.bot.current_time.replace(
            hour=randint(2, 7), minute=randint(1, 59), second=0, microsecond=0
        ) + timedelta(days=1)

        guild = await Guild.get(pk=interaction.guild_id)

        if not guild.is_premium:
            if await Scrim.filter(guild_id=guild.pk).count() >= SCRIMS_LIMIT:
                v = RequirePremiumView(
                    f"You have reached the maximum limit of '{SCRIMS_LIMIT} scrims', Upgrade to Quotient Pro to unlock unlimited scrims."
                )

                return await interaction.followup.send(
                    embed=v.premium_embed,
                    view=v,
                )

        await self.view.record.save()
        await self.view.bot.reminders.create_timer(self.view.record.reg_start_time, "scrim_open", scrim_id=self.view.record.id)
        await self.view.bot.reminders.create_timer(
            self.view.record.autoclean_channel_time,
            "autoclean_scrims_channel",
            scrim_id=self.view.record.id,
        )
        await self.view.bot.reminders.create_timer(
            self.view.record.match_start_time, "scrims_match_start", scrim_id=self.view.record.id
        )

        self.view.stop()
        await interaction.followup.send(
            embed=self.view.bot.success_embed(
                f"Scrim was successfully created. (Registration: {discord.utils.format_dt(self.view.record.reg_start_time)})"
            ),
            ephemeral=True,
        )

        from ..main_panel import ScrimsMainPanel

        view = ScrimsMainPanel(self.ctx)
        view.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.view.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )
        view.message = await self.view.message.edit(embed=await view.initial_msg(), view=view)
