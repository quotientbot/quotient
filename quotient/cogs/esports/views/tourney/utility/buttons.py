import discord
from cogs.esports.views.tourney import TourneyBtn
from cogs.premium import Feature, can_use_feature, prompt_premium_plan
from discord.ext import commands
from lib import INFO, send_error_embed, text_channel_input

from quotient.models import Scrim, Tourney

from .callbacks import (
    edit_confirm_channel,
    edit_group_size,
    edit_reactions,
    edit_required_mentions,
    edit_success_role,
    edit_total_slots,
)


class SetRegChannel(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        channel = await text_channel_input(interaction, "Please select the channel you want to set as the registration channel.")

        if not channel:
            return

        if await Tourney.filter(registration_channel_id=channel.id).exists():
            return await send_error_embed(interaction.channel, "That channel is already in use for another tourney.", 5)

        if await Scrim.filter(registration_channel_id=channel.id).exists():
            return await send_error_embed(interaction.channel, "That channel is already in use for a scrim.", 5)

        self.view.record.registration_channel_id = channel.id

        if not self.view.record.confirm_channel_id:
            try:
                self.view.record.confirm_channel_id = next(
                    (c.id for c in channel.category.text_channels if "confirm" in c.name.lower())
                )
            except (StopIteration, AttributeError):
                pass

        if not self.view.record.success_role_id:
            for r in channel.guild.roles:
                if "confirm" in r.name.lower():
                    self.view.record.success_role_id = r.id
                    break

        await self.view.refresh_view()


class SetConfirmChannel(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_confirm_channel(self, interaction)


class SetMentions(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_required_mentions(self, interaction)


class SetTotalSlots(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_total_slots(self, interaction)


class SetGroupSize(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_group_size(self, interaction)


class SetSuccessRole(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        await edit_success_role(self, interaction)


class SetReactions(TourneyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> any:
        await edit_reactions(self, interaction)


class DiscardChanges(TourneyBtn):
    def __init__(self, ctx: commands.Context, label="Back", row: int = None, **kwargs):
        super().__init__(ctx=ctx, style=discord.ButtonStyle.red, label=label, row=row, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        from ..main_panel import TourneysMainPanel

        self.view.stop()

        v = TourneysMainPanel(self.ctx)
        v.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.view.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class SaveTourney(TourneyBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.green, label="Save Tourney", emoji="📁", disabled=True)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            await self.view.record.setup_logs_and_slotm(interaction.user)
        except Exception as e:
            return await interaction.followup.send(
                embed=self.view.bot.error_embed(f"An error occurred while creating tourney: {e}"),
                view=self.view.bot.contact_support_view(),
            )

        is_allowed, min_tier = await can_use_feature(Feature.TOURNEY_CREATE, self.ctx.guild.id)
        if not is_allowed:
            return await prompt_premium_plan(interaction, f"Upgrade to min **__{min_tier.name}__** tier to create more tournaments.")

        await self.view.record.save()

        self.view.stop()
        await interaction.followup.send(
            embed=self.view.bot.success_embed(f"Tourney was successfully created.\n\n`Click start button to start registrations.`"),
            ephemeral=True,
        )

        from ..main_panel import TourneysMainPanel

        view = TourneysMainPanel(self.ctx)
        view.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.view.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )
        view.message = await self.view.message.edit(embed=await view.initial_msg(), view=view)
