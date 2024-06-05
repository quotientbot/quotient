from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from datetime import datetime, timedelta
from random import randint

import discord
from cogs.premium import SCRIMS_LIMIT, RequirePremiumView
from discord import app_commands
from discord.ext import commands
from lib import parse_natural_time
from models import Scrim

from ..views.scrims.edit import ScrimsEditPanel

__all__ = ("ScrimsSlash",)


class ScrimSlashCommands(commands.GroupCog, name="scrims"):
    def __init__(self, bot: Quotient):
        self.bot = bot

        super().__init__()

    def can_use_scrims_command():
        async def predicate(inter: discord.Interaction) -> bool:
            if not any((inter.user.guild_permissions.manage_guild, Scrim.is_ignorable(inter.user))):
                await inter.response.send_message(
                    embed=discord.Embed(
                        color=discord.Color.red(),
                        description=f"You need `scrims-mod` role or `Manage-Server` permissions to use this command.",
                    )
                )
                return False

            return True

        return app_commands.check(predicate)

    @app_commands.command(name="create", description="Create a new scrim.")
    @app_commands.guild_only()
    @app_commands.describe(
        registration_channel="The channel where users will register for the scrim.",
        slotlist_channel="The channel where the slotlist will be posted.",
        success_role="The role to be given to the users who successfully register.",
        required_mentions="The number of mentions required for successful registration.",
        total_slots="The total number of slots available for the scrim.",
        reg_start_time="The time at which the registration should be started. Ex: 3:00 PM, 9:30 AM, etc",
    )
    @can_use_scrims_command()
    @app_commands.checks.bot_has_permissions(administrator=True)
    @app_commands.rename(
        registration_channel="registration-channel",
        slotlist_channel="slotlist-channel",
        success_role="success-role",
        required_mentions="required-mentions",
        total_slots="total-slots",
        reg_start_time="registration-start-time",
    )
    async def create_new_scrim(
        self,
        inter: discord.Interaction,
        registration_channel: discord.TextChannel,
        slotlist_channel: discord.TextChannel,
        success_role: discord.Role,
        required_mentions: app_commands.Range[int, 0, 5],
        total_slots: app_commands.Range[int, 1, 30],
        reg_start_time: str,
    ):
        await inter.response.defer(thinking=True, ephemeral=False)

        if not await self.bot.is_pro_guild(inter.guild.id):
            if await Scrim.filter(guild_id=inter.guild.id).count() >= SCRIMS_LIMIT:
                v = RequirePremiumView(
                    f"You have reached the maximum limit of '{SCRIMS_LIMIT} scrims', Upgrade to Quotient Pro to unlock unlimited scrims."
                )
                return await inter.followup.send(
                    embed=v.premium_embed,
                    view=v,
                )

        if await Scrim.exists(registration_channel_id=registration_channel.id):
            return await inter.followup.send(
                embed=self.bot.error_embed(
                    f"A scrim already exists in {registration_channel.mention}, please use another channel."
                ),
                view=self.bot.contact_support_view(),
            )

        if not success_role.is_assignable():
            return await inter.followup.send(
                embed=self.bot.error_embed(
                    f"{success_role.mention} is not assignable, Make sure my role is above the role you provided."
                ),
                view=self.bot.contact_support_view(),
            )

        if success_role >= inter.user.top_role and not inter.user.id == inter.guild.owner_id:
            return await inter.followup.send(
                embed=self.bot.error_embed(
                    f"{success_role.mention} is higher than your top role ({inter.user.top_role.mention}), you can't use that role."
                ),
                view=self.bot.contact_support_view(),
            )

        if any(
            (
                success_role.permissions.administrator,
                success_role.permissions.manage_guild,
                success_role.permissions.manage_roles,
                success_role.permissions.manage_channels,
                success_role.permissions.manage_messages,
                success_role.permissions.kick_members,
                success_role.permissions.ban_members,
            )
        ):
            return await inter.followup.send(
                embed=self.bot.error_embed(f"{success_role.mention} has dangerous permissions, you can't use that role."),
                view=self.bot.contact_support_view(),
            )

        try:
            registration_start_time = parse_natural_time(reg_start_time)

        except TypeError:
            return await inter.followup.send(
                embed=self.bot.error_embed(f"Invalid time format. Please try again.").set_image(
                    url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif"
                )
            )

        autoclean_time = self.bot.current_time.replace(
            hour=randint(3, 7), minute=randint(1, 59), second=0, microsecond=0
        ) + timedelta(days=1)

        scrim = Scrim(
            guild_id=inter.guild.id,
            name=f"Quotient Scrims",
            registration_channel_id=registration_channel.id,
            slotlist_channel_id=slotlist_channel.id,
            success_role_id=success_role.id,
            required_mentions=required_mentions,
            total_slots=total_slots,
            reg_start_time=registration_start_time,
            autoclean_time=autoclean_time,
        )

        try:
            await scrim.setup_logs()
        except Exception as e:
            return await inter.followup.send(
                embed=self.bot.error_embed(f"An error occurred while creating scrim: {e}"),
                view=self.bot.contact_support_view(),
            )
        await scrim.save()
        await self.bot.reminders.create_timer(scrim.reg_start_time, "scrim_open", scrim_id=scrim.id)
        await self.bot.reminders.create_timer(scrim.autoclean_time, "autoclean", scrim_id=scrim.id)

        e = discord.Embed(
            color=self.bot.color,
            url=self.bot.config("SUPPORT_SERVER_LINK"),
            title="Scrim created successfully!",
            description=(
                f"**Registration Channel:** {registration_channel.mention}\n"
                f"**Slotlist Channel:** {slotlist_channel.mention}\n"
                f"**Success Role:** {success_role.mention}\n"
                f"**Required Mentions:** `{required_mentions}`\n"
                f"**Total Slots:** `{total_slots}`\n"
                f"**Open Time:** {discord.utils.format_dt(scrim.reg_start_time,'f')}\n"
                f"**Autoclean Time:** {discord.utils.format_dt(autoclean_time,'f')}\n"
            ),
        )
        e.set_footer(text=f"Get more info, using `{self.bot.default_prefix} s` command.")

        await inter.followup.send(embed=e)

    @app_commands.command(name="settings", description="Change the settings of a scrim.")
    @app_commands.guild_only()
    @app_commands.describe(registration_channel="Registration Channel of the scrim you want to edit.")
    @can_use_scrims_command()
    async def scrim_settings(self, inter: discord.Interaction, registration_channel: discord.TextChannel):
        await inter.response.defer(thinking=True, ephemeral=False)
        record = await Scrim.get_or_none(registration_channel_id=registration_channel.id)
        if not record:
            return await inter.followup.send(
                embed=self.bot.error_embed(f"No Scrim found in the {registration_channel.mention}"),
                view=self.bot.contact_support_view(),
            )

        ctx = commands.Context.from_interaction(inter)
        view = ScrimsEditPanel(self.bot, ctx, record)

        view.message = await inter.followup.send(embed=view.initital_embed, view=view)

    @app_commands.command(name="delete", description="Delete a scrim.")
    @app_commands.guild_only()
    @app_commands.describe(registration_channel="Registration Channel of the scrim you want to delete.")
    @app_commands.rename(registration_channel="registration-channel")
    @can_use_scrims_command()
    async def delete_scrim(self, inter: discord.Interaction, registration_channel: discord.TextChannel):
        await inter.response.defer(thinking=True, ephemeral=False)

        record = await Scrim.get_or_none(registration_channel_id=registration_channel.id)
        if not record:
            return await inter.followup.send(
                embed=self.bot.error_embed("No Scrim found in the {0}.".format(registration_channel.mention)),
                view=self.bot.contact_support_view(),
            )

        await record.full_delete()
        await inter.followup.send(embed=self.bot.success_embed("Scrim deleted successfully."))
