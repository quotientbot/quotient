import discord
from core import QuoView
from discord.ext import commands
from lib import integer_input_modal, text_channel_input

from quotient.cogs.premium import Feature, can_use_feature, prompt_premium_plan
from quotient.models import TagCheck


class TagCheckPanel(QuoView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx=ctx, timeout=100)

    async def initial_msg(self) -> discord.Embed:
        records = await TagCheck.filter(guild_id=self.ctx.guild.id).order_by("id")

        e = discord.Embed(color=self.bot.color, title="Tag Check Settings", url=self.bot.config("SUPPORT_SERVER_LINK"), description="")

        for idx, record in enumerate(records, start=1):
            e.description += f"`{idx}.` {record}\n"

        if not records:
            e.description = "```No Tag Check channel found```"

        return e

    @discord.ui.button(label="#Set Channel", style=discord.ButtonStyle.primary)
    async def set_tc_channel(self, inter: discord.Interaction, btn: discord.ui.Button):

        no_of_mentions = await integer_input_modal(
            inter, title="Required Mentons", label="Required mentions for tagcheck?", placeholder="4", default=4
        )
        if not no_of_mentions:
            return

        ch = await text_channel_input(inter, message="Please select a channel to set tag-check in.")
        if not ch:
            return

        perms = ch.permissions_for(inter.guild.me)
        if not all([perms.manage_messages, perms.embed_links, perms.add_reactions, perms.use_external_emojis]):
            return await inter.followup.send(
                embed=self.bot.error_embed(
                    description="Please allow me `Manage Messages`, `Embed Links`, `Add Reactions` & `Use External Emojis` permission in {}.".format(
                        ch.mention
                    ),
                    title="Permissions Required!",
                ),
                ephemeral=True,
            )

        if await TagCheck.filter(guild_id=inter.guild_id, channel_id=ch.id).exists():
            return await inter.followup.send(
                embed=self.bot.error_embed(
                    description="Tag Check channel already exists in {}".format(ch.mention),
                    title="Channel Already Exists!",
                ),
                ephemeral=True,
            )

        is_allowed, min_tier = await can_use_feature(Feature.TAG_CHECK_CREATE, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter,
                f"Your server has reached the limit of tag checks allowed. Upgrade to min **__{min_tier.name}__** tier to create more tag checks.",
            )

        await TagCheck.create(guild_id=inter.guild_id, channel_id=ch.id, required_mentions=no_of_mentions)
        self.bot.cache.tagcheck_channel_ids.add(ch.id)
        await inter.followup.send(
            embed=self.bot.success_embed(
                description=f"Tag Check channel set in {ch.mention} with `{no_of_mentions}` required mentions.",
                title="Channel Set!",
            ),
            ephemeral=True,
        )

        v = TagCheckPanel(self.ctx)
        v.message = await self.message.edit(embed=await v.initial_msg(), view=v)

    @discord.ui.button(label="Remove Tag Check", style=discord.ButtonStyle.danger)
    async def remove_tc_channel(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer(ephemeral=True, thinking=True)

        ch = await text_channel_input(inter, message="Please select a channel to remove tag-check from.")
        if not ch:
            return

        record = await TagCheck.get_or_none(guild_id=inter.guild_id, channel_id=ch.id)
        if not record:
            return await inter.followup.send(
                embed=self.bot.error_embed(f"Tag Check channel not found in {ch.mention}"), ephemeral=True
            )

        await record.delete()
        self.bot.cache.tagcheck_channel_ids.discard(ch.id)
        await inter.followup.send(embed=self.bot.success_embed(f"Tag Check channel removed from {ch.mention}"), ephemeral=True)

        v = TagCheckPanel(self.ctx)
        v.message = await self.message.edit(embed=await v.initial_msg(), view=v)
