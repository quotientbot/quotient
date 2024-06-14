from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from datetime import timedelta
from random import randint

import discord
from cogs.premium import SCRIMS_LIMIT, RequirePremiumView
from discord import app_commands
from discord.ext import commands
from lib import parse_natural_time
from models import Guild, Scrim

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
        required_mentions="The number of mentions required for successful registration.",
        total_slots="The total number of slots available for the scrim.",
        reg_start_time="The time at which the registration should be started. Ex: 3:00 PM, 9:30 AM, etc",
    )
    @can_use_scrims_command()
    @app_commands.checks.bot_has_permissions(administrator=True)
    @app_commands.rename(
        registration_channel="registration-channel",
        slotlist_channel="slotlist-channel",
        required_mentions="required-mentions",
        total_slots="total-slots",
        reg_start_time="registration-start-time",
    )
    async def create_new_scrim(
        self,
        inter: discord.Interaction,
        registration_channel: discord.TextChannel,
        slotlist_channel: discord.TextChannel,
        required_mentions: app_commands.Range[int, 0, 5],
        total_slots: app_commands.Range[int, 1, 30],
        reg_start_time: str,
    ):
        await inter.response.defer(thinking=True, ephemeral=False)

        guild = await Guild.get(pk=inter.guild_id).prefetch_related("scrims")

        if not guild.is_premium:
            if len(guild.scrims) >= SCRIMS_LIMIT:
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
            guild=guild,
            name=f"Quotient Scrims",
            registration_channel_id=registration_channel.id,
            slotlist_channel_id=slotlist_channel.id,
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
                f"**Required Mentions:** `{required_mentions}`\n"
                f"**Total Slots:** `{total_slots}`\n"
                f"**Open Time:** {discord.utils.format_dt(scrim.reg_start_time,'f')}\n"
                f"**Autoclean Time:** {discord.utils.format_dt(autoclean_time,'f')}\n"
            ),
        )
        e.set_footer(text=f"Get more info, using `{self.bot.default_prefix} s` command.")

        await inter.followup.send(embed=e)

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

    @app_commands.command(name="idp", description="Share ID/Pass with teams of a scrim.")
    @app_commands.guild_only()
    @app_commands.describe(
        registration_channel="The channel where users will register for the scrim.",
        room_id="The Room ID of the scrim.",
        password="The Password of the scrim.",
        map_name="The Map Name of the scrim.",
        ping_leaders="Whether to ping team leaders or not.",
    )
    @app_commands.rename(
        registration_channel="registration-channel",
        room_id="room-id",
        map_name="map-name",
        ping_leaders="ping-leaders",
    )
    @can_use_scrims_command()
    async def share_scrims_idp(
        self,
        inter: discord.Interaction,
        registration_channel: discord.TextChannel,
        room_id: str,
        password: str,
        map_name: str,
        ping_leaders: T.Literal["Yes", "No"],
    ):
        await inter.response.defer(thinking=True, ephemeral=False)
        record = await Scrim.get_or_none(registration_channel_id=registration_channel.id)
        if not record:
            return await inter.followup.send(
                embed=self.bot.error_embed("No Scrim found in the {0}.".format(registration_channel.mention)),
                view=self.bot.contact_support_view(),
            )
        await inter.followup.send(embed=self.bot.success_embed(f"Scrim ID: {record.id}"))

    @app_commands.command(
        name="announce",
        description="Announce something to teams of a scrim (Mentions all team leaders).",
    )
    @app_commands.guild_only()
    @app_commands.describe(
        registration_channel="The channel where users will register for the scrim.",
        message="The message you want to announce.",
    )
    @app_commands.rename(registration_channel="registration-channel")
    @can_use_scrims_command()
    async def announce_scrim(self, inter: discord.Interaction, registration_channel: discord.TextChannel, message: str):
        await inter.response.defer(thinking=True, ephemeral=False)

        record = await Scrim.get_or_none(registration_channel_id=registration_channel.id)
        if not record:
            return await inter.followup.send(
                embed=self.bot.error_embed("No Scrim found in the {0}.".format(registration_channel.mention)),
                view=self.bot.contact_support_view(),
            )

        await inter.followup.send(embed=self.bot.success_embed("Announcement sent successfully."))
