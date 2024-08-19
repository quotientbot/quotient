import discord
from cogs.premium import Feature, can_use_feature, prompt_premium_plan
from discord.ext import commands

from quotient.lib import INFO
from quotient.models import SSverify

from . import SsVerifyView
from .edit_settings import EditSsVerifySettings
from .setup_panel import CreateSsVerify


class SsVerifyMainPanel(SsVerifyView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, timeout=100)

    async def initial_msg(self) -> discord.Embed:
        self.add_item(
            discord.ui.Button(
                label="Contact Support",
                style=discord.ButtonStyle.link,
                url=self.bot.config("SUPPORT_SERVER_LINK"),
                emoji=INFO,
            )
        )

        records = await SSverify.filter(guild_id=self.ctx.guild.id).order_by("id").prefetch_related("entries")

        e = discord.Embed(
            color=self.bot.color, title="Quotient's Screenshots Manager", url=self.bot.config("SUPPORT_SERVER_LINK"), description=""
        )

        for idx, record in enumerate(records, start=1):
            e.description += f"`{idx}.` {record} — Entries: `{sum(1 for _ in record.entries)}`\n"

        if not records:
            e.description += "```Click 'Setup SSVerify' to setup ss verification```"

            for i, child in enumerate(self.children):  # Disable every btn except first & last.
                if i != 0 and i != len(self.children) - 1:
                    child.disabled = True

        return e

    @discord.ui.button(label="Setup SSVerify", style=discord.ButtonStyle.blurple)
    async def setup_ssverify(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        is_allowed, min_tier = await can_use_feature(Feature.SSVERIFY_CREATE, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter,
                f"Your server has reached the limit of ssverifcation allowed. Upgrade to min **__{min_tier.name}__** tier to create more.",
            )

        self.stop()
        v = CreateSsVerify(self.ctx)
        v.message = await self.message.edit(embed=v.initial_msg(), view=v)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.green)
    async def edit_ssverify_settings(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer()

        records = await SSverify.filter(guild_id=inter.guild_id).order_by("id").prefetch_related("entries")
        if not records:
            return await inter.followup.send("No ssverify setup found.", ephemeral=True)

        self.stop()
        v = EditSsVerifySettings(self.ctx, records[0])
        v.message = await self.message.edit(embed=await v.initial_msg(), view=v)
