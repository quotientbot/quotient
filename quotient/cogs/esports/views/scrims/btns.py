import os
from datetime import timedelta
from random import randint

import discord
from cogs.premium import SCRIMS_LIMIT, RequirePremiumView
from discord.ext import commands
from lib import (
    integer_input_modal,
    send_error_embed,
    send_simple_embed,
    text_channel_input,
    text_input,
    time_input_modal,
)
from models import Guild, Scrim

from ..scrims import ScrimsBtn
from .selectors import WeekDaysSelector


class SetRegChannel(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await send_simple_embed(
            interaction.channel, "Please mention the channel you want to set as the registration channel."
        )
        channel = await text_channel_input(self.ctx, delete_after=True)
        await m.delete(delay=0)

        if await Scrim.filter(registration_channel_id=channel.id).exists():
            return await send_error_embed(interaction.channel, "That channel is already in use for another scrim.", 5)

        self.view.record.registration_channel_id = channel.id

        await self.view.refresh_view()


class SetMentions(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        req_mentions = await integer_input_modal(
            interaction,
            title="Required Mentions",
            label="How many mentions are required to register?",
            placeholder="Enter a number in range 0-5",
            default=self.view.record.required_mentions,
        )

        if req_mentions is None:
            return await send_error_embed(interaction.channel, "You failed to enter a valid number! Please try again.", 5)

        if not 0 <= req_mentions <= 5:
            return await send_error_embed(interaction.channel, "Mentions must be in range 0-5.", 5)

        self.view.record.required_mentions = req_mentions

        await self.view.refresh_view()


class SetTotalSlots(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        total_slots = await integer_input_modal(
            interaction,
            title="Total Slots",
            label="How many total slots are there?",
            placeholder="Enter a number in range 1-30",
            default=self.view.record.total_slots,
        )

        if total_slots is None:
            return await send_error_embed(interaction.channel, "You failed to enter a valid number! Please try again.", 5)

        if not 1 <= total_slots <= 30:
            return await send_error_embed(interaction.channel, "Total Slots must be in range 1-30.", 5)

        self.view.record.total_slots = total_slots

        await self.view.refresh_view()


class SetRegStartTime(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        reg_start_time = await time_input_modal(
            interaction,
            title="Registration Start Time (IST - UTC+5:30)",
            label="Enter registration start time.",
            default=self.view.record.reg_start_time.strftime("%I:%M%p") if self.view.record.reg_start_time else None,
        )

        if reg_start_time is None:
            return await send_error_embed(
                interaction.channel,
                "You failed to enter registration start time in valid format! Take a look at the examples below:",
                delete_after=5,
                image_url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif",
            )

        self.view.record.reg_start_time = reg_start_time
        await self.view.refresh_view()


class SetRegOpenDays(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        v = discord.ui.View(timeout=100)
        v.add_item(WeekDaysSelector())

        await interaction.response.send_message(
            "Select weekdays on which registration should be opened:", view=v, ephemeral=True
        )
        await v.wait()

        if v.selected_days:
            self.view.record.registration_open_days = [int(d) for d in v.selected_days]
            await self.view.refresh_view()


class SetReactions(ScrimsBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        await interaction.response.defer()

        guild = await Guild.get(pk=interaction.guild_id)

        if not guild.is_premium:
            v = RequirePremiumView(f"Upgrade to Quotient Pro to use custom reactions.")

            return await interaction.followup.send(embed=v.premium_embed, view=v, ephemeral=True)

        e = discord.Embed(color=int(os.getenv("DEFAULT_COLOR")), title="Edit scrims emojis")

        e.description = (
            "Which emojis do you want to use for tick and cross in scrims registrations? Note that both emojis must be in this server.\n\n"
            "`Please enter two emojis and separate them with a comma`"
        )

        e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/888097255607906354/unknown.png")
        e.set_footer(text="The first emoji must be the emoji for tick mark.")

        m = await interaction.followup.send(embed=e)
        emojis = await text_input(self.ctx, delete_after=True)

        await m.delete(delay=0)

        emojis = emojis.strip().split(",")
        if not len(emojis) == 2:
            return await send_error_embed(interaction.channel, "You didn't enter emojis in correct format.", 5)

        check, cross = emojis

        for idx, emoji in enumerate(emojis, start=1):
            try:
                await self.view.message.add_reaction(emoji.strip())
                await self.view.message.clear_reactions()
            except discord.HTTPException:
                return await interaction.followup.send(
                    embed=self.view.bot.error_embed(
                        f"Emoji {idx} is not valid, Please make sure it is present in this server."
                    ),
                    ephemeral=True,
                )

        self.view.record.reactions = [check.strip(), cross.strip()]
        await self.view.refresh_view()
        # await self.view.record.confirm_all_scrims(self.ctx, emojis=self.view.record.emojis)


class DiscardChanges(ScrimsBtn):
    def __init__(self, ctx: commands.Context, label="Back", row: int = None):
        super().__init__(ctx=ctx, style=discord.ButtonStyle.red, label=label, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from .main import ScrimsMainPanel

        self.view.stop()
        v = ScrimsMainPanel(self.ctx)
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
        await self.view.bot.reminders.create_timer(
            self.view.record.reg_start_time, "scrim_open", scrim_id=self.view.record.id
        )
        await self.view.bot.reminders.create_timer(
            self.view.record.autoclean_channel_time,
            "autoclean_scrims_channel",
            scrim_id=self.view.record.id,
        )

        self.view.stop()
        await interaction.followup.send(
            embed=self.view.bot.success_embed(
                f"Scrim was successfully created. (Registration: {discord.utils.format_dt(self.view.record.reg_start_time)})"
            ),
            ephemeral=True,
        )

        from .main import ScrimsMainPanel

        view = ScrimsMainPanel(self.ctx)
        view.message = await self.view.message.edit(embed=await view.initial_msg(), view=view)
