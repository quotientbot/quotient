import asyncio
from datetime import timedelta

import discord
from cogs.premium import views
from core import QuoView
from discord.ext import commands
from humanize import precisedelta
from lib import simple_time_input, text_channel_input

from quotient.cogs.premium import Feature, can_use_feature, prompt_premium_plan
from quotient.models import AutoPurge


class AutopurgeView(QuoView):
    def __init__(self, ctx: commands.Context):
        super().__init__(ctx)

    async def initial_msg(self):
        records = await AutoPurge.filter(guild_id=self.ctx.guild.id)

        e = discord.Embed(
            color=self.bot.color,
            title="Auto Purge Settings",
        )
        e.description = (
            "Once a message is sent in the specified channel, "
            "the bot will wait for the designated time period before automatically deleting the message.\n\n"
        )

        if not records:
            e.description += "```Click 'Set New Channel' to get started.```"
            self.children[1].disabled = True
            return e

        self.children[1].disabled = False

        for idx, record in enumerate(records, start=1):
            e.description += f"`[{idx:02}]` {getattr(record.channel, 'mention', 'deleted-channel')}: `{precisedelta(timedelta(seconds=record.delete_after))}`\n"

        return e

    async def refresh_view(self):
        try:
            await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException as e:
            raise e

    @discord.ui.button(label="Set New Channel", style=discord.ButtonStyle.primary)
    async def set_ap_channel(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer(thinking=True, ephemeral=True)

        # Check if guild can create more ap channels
        is_allowed, min_tier = await can_use_feature(Feature.AUTOPURGE_CREATE, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter, text=f"You need to be on **{min_tier.name}** tier to setup more 'Auto Purge' channels."
            )

        try:
            channel = await text_channel_input(inter, "Please mention the channel you want to set autopurge.")
        except asyncio.TimeoutError:
            return await inter.followup.send(embed=self.bot.error_embed("You failed to select a channel in time. Try again!"))

        if not channel.permissions_for(inter.user).manage_messages:
            return await inter.followup.send(
                embed=self.bot.error_embed(f"You must have`Manage Messages` permission in {channel.mention}."),
                ephemeral=True,
            )
        check = await AutoPurge.filter(channel_id=channel.id).exists()
        if check:
            return await inter.followup.send(embed=self.bot.error_embed("This channel is already set for AutoPurge."))

        await inter.followup.send(
            embed=self.bot.simple_embed("Please input the time for the message to be deleted.\n\n```Example: 10s, 10m, 10h, etc.```"),
            ephemeral=True,
        )
        try:
            time_in_seconds = await simple_time_input(self.ctx, delete_after=True)
        except asyncio.TimeoutError:
            return await inter.followup.send(embed=self.bot.error_embed("You failed to input in time. Try again!"))

        if time_in_seconds <= 5 or time_in_seconds > 604800:
            return await inter.followup.send(
                embed=self.bot.error_embed("Delete Time must be more than 5s and less than 7d."),
                ephemeral=True,
            )

        # Check if guild can create more ap channels
        is_allowed, min_tier = await can_use_feature(Feature.AUTOPURGE_CREATE, inter.guild_id)
        if not is_allowed:
            return await prompt_premium_plan(
                inter, text=f"You need to be on **{min_tier.name}** tier to setup more 'Auto Purge' channels."
            )

        await AutoPurge.create(guild_id=inter.guild_id, channel_id=channel.id, delete_after=time_in_seconds)
        self.bot.cache.autopurge_channel_ids.add(channel.id)

        await inter.followup.send(
            embed=self.bot.success_embed(
                f"Successfully set {channel.mention}, every new msg will be deleted after `{precisedelta(timedelta(seconds=time_in_seconds))}`."
            ),
            ephemeral=True,
        )
        await self.refresh_view()

    @discord.ui.button(label="Remove Channel", style=discord.ButtonStyle.danger)
    async def del_ap_channel(self, inter: discord.Interaction, btn: discord.ui.Button):
        await inter.response.defer(thinking=True, ephemeral=True)

        await inter.followup.send(
            embed=self.bot.simple_embed("Please select the channel you want to remove from AutoPurge."),
            ephemeral=True,
        )
        try:
            channel = await text_channel_input(inter, "Please mention the channel you want to remove from AutoPurge.")
        except asyncio.TimeoutError:
            return await inter.followup.send(
                embed=self.bot.error_embed("You failed to select a channel in time. Try again!"),
                ephemeral=True,
            )

        record = await AutoPurge.filter(channel_id=channel.id).first()
        if not record:
            return await inter.followup.send(
                embed=self.bot.error_embed("This channel is not set for AutoPurge."),
                ephemeral=True,
            )

        await record.delete()
        self.bot.cache.autopurge_channel_ids.discard(channel.id)
        await inter.followup.send(
            embed=self.bot.success_embed(f"Successfully removed {channel.mention} from AutoPurge."),
            ephemeral=True,
        )
        await self.refresh_view()
