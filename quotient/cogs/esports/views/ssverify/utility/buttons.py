import discord
from discord.ext import commands

from quotient.cogs.premium import Feature, can_use_feature, prompt_premium_plan
from quotient.lib import (
    INSTAGRAM,
    NEXT_PAGE,
    PREVIOUS_PAGE,
    YOUTUBE,
    guild_role_input,
    integer_input_modal,
    regional_indicator,
    role_has_harmful_permissions,
    send_error_embed,
    text_channel_input,
    text_input_modal,
)
from quotient.models import ScreenshotType, SSverify

from .. import SsVerifyBtn


class ScreenshotTypeSelector(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Select the type of screenshot to expect ...",
            options=[
                discord.SelectOption(label="Youtube", value=ScreenshotType.YT, emoji=YOUTUBE),
                discord.SelectOption(label="Instagram", value=ScreenshotType.INSTA, emoji=INSTAGRAM),
                discord.SelectOption(label="Any Screenshot", value=ScreenshotType.ANY, emoji=regional_indicator("A")),
                discord.SelectOption(label="Custom", value=ScreenshotType.CUSTOM, emoji=regional_indicator("C")),
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_ss_type = ScreenshotType(interaction.data["values"][0])
        self.view.possible_keywords = []

        if self.view.selected_ss_type == ScreenshotType.CUSTOM:
            keywords = await text_input_modal(
                interaction,
                title="Set Keywords",
                label="Keywords to expect in the screenshot",
                placeholder="(,) comma separated possible keywords...",
                max_length=250,
            )
            if not keywords:
                return await interaction.response.send_message("Cancelled", ephemeral=True)

            self.view.possible_keywords = keywords.lower().strip().split(",")

        else:
            await interaction.response.defer()

        self.view.stop()


class SetRegChannel(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()

        channel = await text_channel_input(inter, "Please select the channnel you want to use for ssverification.")
        if not channel:
            return

        if await SSverify.filter(channel_id=inter.channel_id).exists():
            return await send_error_embed(inter.channel, "This channel is already an ssverification channel.", delete_after=7)

        perms = channel.permissions_for(inter.guild.me)
        if not all((perms.embed_links, perms.external_emojis, perms.add_reactions)):
            return await send_error_embed(
                inter.channel,
                "I need the following permissions in the selected channel: `Embed Links`, `External Emojis`, `Add Reactions`",
                delete_after=7,
            )

        self.view.record.channel_id = channel.id

        await self.view.refresh_view()


class SetSuccessRole(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()

        role = await guild_role_input(inter, "Please select the role you want to give to users who successfully verify.")
        if not role:
            return

        if role_has_harmful_permissions(role):
            return await send_error_embed(
                inter.channel,
                f"The role {role.mention} has harmful permissions in the server, please remove them before continuing.",
                delete_after=7,
            )

        if role.position >= inter.guild.me.top_role.position:
            return await send_error_embed(
                inter.channel, "I can't give a role higher than my top role, please move the role below mine.", delete_after=7
            )

        self.view.record.role_id = role.id

        await self.view.refresh_view()


class SetRequiredSS(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        required_ss = await integer_input_modal(
            inter, title="Set Required SS", label="Number of screenshots required to verify?", default=self.view.record.required_ss
        )
        if not required_ss:
            return

        if required_ss not in range(1, 6):
            return await send_error_embed(inter.channel, "The number of screenshots required must be between 1 and 5.", delete_after=7)

        self.view.record.required_ss = required_ss

        await self.view.refresh_view()


class SetScreenshotType(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        v = discord.ui.View(timeout=100)
        v.add_item(ScreenshotTypeSelector())
        await inter.response.send_message("Select the type of screenshot to expect ...", view=v, ephemeral=True)

        await v.wait()

        if not (selected_ss_type := v.selected_ss_type):
            return

        self.view.record.screenshot_type = selected_ss_type
        self.view.record.possible_keywords = v.possible_keywords
        await self.view.refresh_view()


class SetEntityName(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        entity_name = await text_input_modal(
            inter,
            title="Set Page Name",
            label="Enter the exact name of your yt/other channel",
            max_length=50,
            default=self.view.record.entity_name,
        )
        if not entity_name:
            return

        self.view.record.entity_name = entity_name

        await self.view.refresh_view()


class SetEntityLink(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        entity_link = await text_input_modal(
            inter,
            title="Set Page Link",
            label="Enter the link to your yt / other channel",
            max_length=200,
            default=self.view.record.entity_link,
        )
        if not entity_link:
            return

        self.view.record.entity_link = entity_link

        await self.view.refresh_view()


class SetAllowDuplicateSS(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()

        self.view.record.allow_duplicate_ss = not self.view.record.allow_duplicate_ss

        await self.view.refresh_view()


class SetSuccessMessage(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, emoji: str):
        super().__init__(ctx, emoji=emoji)

    async def callback(self, inter: discord.Interaction):
        success_message = await text_input_modal(
            inter,
            title="Set Success Message",
            label="Msg to send when user successfully verifies",
            max_length=500,
            default=self.view.record.success_message,
            input_type="long",
        )
        if not success_message:
            return

        self.view.record.success_message = success_message

        await self.view.refresh_view()


class DiscardButton(SsVerifyBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, label="Cancel", style=discord.ButtonStyle.red)

    async def callback(self, interaction: discord.Interaction):
        from ..main_panel import SsVerifyMainPanel

        await interaction.response.defer()
        self.view.stop()

        v = SsVerifyMainPanel(self.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class DeleteSsVerifySetup(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, record: SSverify):
        super().__init__(ctx, label="Delete SSverify", style=discord.ButtonStyle.red)
        self.record = record

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        prompt = await self.view.record.bot.prompt(
            interaction, interaction.user, "Are you sure you want to delete this ssverify setup?"
        )
        if not prompt:
            return await self.view.on_timeout()

        await self.record.full_delete()
        await interaction.followup.send(embed=self.view.record.bot.success_embed("Successfully deleted ssverify."), ephemeral=True)

        return await self.view.on_timeout()


class SaveButton(SsVerifyBtn):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, label="Save & Setup", style=discord.ButtonStyle.green, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        from ..main_panel import SsVerifyMainPanel

        await interaction.response.defer()

        is_allowed, min_tier = await can_use_feature(Feature.SSVERIFY_CREATE, interaction.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                interaction,
                f"Your server has reached the limit of ssverifcation allowed. Upgrade to min **__{min_tier.name}__** tier to create more.",
            )

        await self.view.record.save()
        self.view.record.bot.cache.ssverify_channel_ids.add(self.view.record.channel_id)

        await interaction.followup.send(
            embed=self.view.bot.success_embed(f"Successfully set ssverification in {self.view.record.channel.mention}."),
            ephemeral=True,
        )

        self.view.stop()
        v = SsVerifyMainPanel(self.ctx)
        v.message = await self.view.message.edit(embed=await v.initial_msg(), view=v)


class NextPage(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx=ctx, emoji=NEXT_PAGE, row=row, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_records = await SSverify.filter(guild_id=self.ctx.guild.id).order_by("id")

        current_record_index = [tourney.pk for tourney in all_records].index(self.view.record.pk)

        try:
            next_record = all_records[current_record_index + 1]
        except IndexError:
            next_record = all_records[0]

        if not self.view.record.pk == next_record.pk:
            self.view.record = next_record
            await self.view.refresh_view()


class SkipToPage(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx, label="Skip to...", row=row)

    async def callback(self, interaction: discord.Interaction):

        record_position = await integer_input_modal(
            inter=interaction,
            title="Skip to Page",
            label="Please enter the page no.",
        )

        all_records = await SSverify.filter(guild_id=self.ctx.guild.id).order_by("id")

        if not record_position:
            return

        if record_position > len(all_records):
            return await interaction.followup.send("Invalid page number. Please try again.", ephemeral=True)

        self.view.record = all_records[record_position - 1]
        await self.view.refresh_view()


class PreviousPage(SsVerifyBtn):
    def __init__(self, ctx: commands.Context, row: int = None):
        super().__init__(ctx=ctx, emoji=PREVIOUS_PAGE, row=row, style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        all_records = await SSverify.filter(guild_id=self.ctx.guild.id).order_by("id")

        current_record_index = [tourney.pk for tourney in all_records].index(self.view.record.pk)

        try:
            prev_record = all_records[current_record_index - 1]
        except IndexError:
            prev_record = all_records[-1]

        if not self.view.record.pk == prev_record.pk:
            self.view.record = prev_record
            await self.view.refresh_view()
