from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

from datetime import datetime, timedelta
from random import randint

import dateparser
import discord
from discord import app_commands
from discord.ext import commands

from core import Context
from models import BanLog, Guild, ReservedSlot, Scrim
from utils import Prompt, discord_timestamp, emote, plural, split_list

__all__ = ("ScrimsSlash",)


class ScrimsSelector(discord.ui.Select):
    def __init__(self, placeholder: str, scrims: list[Scrim], multi: bool):
        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=getattr(scrim.registration_channel, "name", "deleted-channel"),  # type: ignore
                    value=scrim.id,
                    description=f"{scrim.name} (ScrimID: {scrim.id})",
                    emoji=emote.TextChannel,
                )
            )

        super().__init__(placeholder=placeholder, options=_options, max_values=len(_options) if multi else 1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in self.options:
            self.view.selected_scrims.discard(option.value)

        for val in self.values:
            self.view.selected_scrims.add(val)


class ScrimsSelector(discord.ui.Select):
    def __init__(self, placeholder: str, scrims: list[Scrim], multi: bool):
        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=getattr(scrim.registration_channel, "name", "deleted-channel"),  # type: ignore
                    value=scrim.id,
                    description=f"{scrim.name} (ScrimID: {scrim.id})",
                    emoji=emote.TextChannel,
                )
            )

        super().__init__(placeholder=placeholder, options=_options, max_values=len(_options) if multi else 1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        for option in self.options:
            self.view.selected_scrims.discard(option.value)

        for val in self.values:
            self.view.selected_scrims.add(val)


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Confirm")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.proceed = True

        for child in self.view.children:
            child.disabled = True

        await interaction.edit_original_response(view=self.view)
        self.view.stop()


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Cancel")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        for child in self.view.children:
            child.disabled = True

        await interaction.edit_original_response(view=self.view)

        self.view.stop()


class ConfirmButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Confirm")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.proceed = True

        for child in self.view.children:
            child.disabled = True

        await interaction.edit_original_response(view=self.view)
        self.view.stop()


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Cancel")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        for child in self.view.children:
            child.disabled = True

        await interaction.edit_original_response(view=self.view)

        self.view.stop()


class ScrimsSlash(commands.GroupCog, name="scrims"):
    def __init__(self, bot: Quotient):
        self.bot = bot

        super().__init__()

    async def can_use_command(self, interaction: discord.Interaction) -> bool:
        if not any(
            (interaction.user.guild_permissions.manage_guild, Scrim.is_ignorable(interaction.user))  # type: ignore # line guarded #25
        ):
            await interaction.response.send_message(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=f"You need `scrims-mod` role or `Manage-Server` permissions to use this command.",
                )
            )
            return False

        return True

    def channel_perms(self, channel: discord.TextChannel) -> bool:
        perms = channel.permissions_for(channel.guild.me)
        return all((perms.manage_channels, perms.manage_permissions))

    def role_perms(self, role: discord.Role) -> bool:
        perms = role.permissions
        return any(
            (
                perms.manage_guild,
                perms.administrator,
                perms.manage_channels,
                perms.manage_roles,
                perms.kick_members,
                perms.ban_members,
            )
        )

    async def show_scrims_selector(
        self,
        interaction: discord.Interaction,
        scrims: list[Scrim],
        multi: bool = False,
        ephemeral: bool = True,
        placeholder: str = "Select scrim(s) to proceed.",
    ):
        if len(scrims) == 1:
            return scrims

        view = discord.ui.View(timeout=100)
        view.selected_scrims = set()
        view.proceed: bool = False

        if len(scrims) <= 25:
            view.add_item(ScrimsSelector(placeholder, scrims, multi=multi))

        else:
            for scrims_chunk in split_list(scrims, 25):
                view.add_item(ScrimsSelector(placeholder, scrims_chunk, multi=multi))

        view.add_item(ConfirmButton())
        view.add_item(CancelButton())

        await interaction.followup.send("Select scrim(s) & press `Confirm`!", view=view, ephemeral=ephemeral)
        await view.wait()

        if not view.proceed:
            return

        return await Scrim.filter(id__in=view.selected_scrims).order_by("id")

    async def reserve_slot(self, scrim: Scrim, num: int, team_name: str, user_id: int = None, expires: datetime = None):
        to_del = await scrim.reserved_slots.filter(num=num).first()
        if to_del:
            await ReservedSlot.filter(pk=to_del.id).delete()

        slot = await ReservedSlot.create(num=num, user_id=user_id, team_name=team_name, expires=expires)
        await scrim.reserved_slots.add(slot)
        if expires and user_id:
            await scrim.bot.reminders.create_timer(
                expires, "scrim_reserve", scrim_id=scrim.id, user_id=user_id, team_name=team_name, num=num
            )

    async def parse_datetime(self, interaction: discord.Interaction, time: str) -> datetime:
        try:
            parsed = dateparser.parse(
                time,
                settings={
                    #  "RELATIVE_BASE": datetime.now(tz=IST),
                    "TIMEZONE": "Asia/Kolkata",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                },
            )

            while self.bot.current_time > parsed:
                parsed = parsed + timedelta(hours=24)

            return parsed

        except TypeError:
            await interaction.followup.send(
                embed=discord.Embed(
                    color=discord.Color.red(), description=f"Invalid time format. Please try again."
                ).set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/958291942062587934/timex.gif")
            )

    @app_commands.command()
    @app_commands.describe(
        registration_channel="The channel where users will register for scrims.",
        slotlist_channel="The channel where slotlist will be posted.",
        success_role="The role that will be given to users who successfully register for scrims.",
        required_mentions="The number of mentions required to register for scrims.",
        total_slots="The total number of slots available for scrims.",
        open_time="The time when registration will be opened.",
    )
    async def create(
        self,
        interaction: discord.Interaction,
        registration_channel: discord.TextChannel,
        slotlist_channel: discord.TextChannel,
        success_role: discord.Role,
        required_mentions: app_commands.Range[int, None, 5],
        total_slots: app_commands.Range[int, 1, 30],
        open_time: str,
    ):
        """Create a scrim."""
        if not await self.can_use_command(interaction):
            return

        await interaction.response.defer(thinking=True, ephemeral=False)

        if not await Guild.filter(pk=interaction.guild_id, is_premium=True).exists():
            if await Scrim.filter(guild_id=interaction.guild_id).count() >= 3:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        color=discord.Color.red(),
                        description=(
                            "You can only create 3 scrims in a server without premium.\n\n"
                            "### Use `qpro` command to activate Quotient Pro."
                        ),
                    )
                )

        if not self.channel_perms(registration_channel):
            return await interaction.followup.send(
                f"{emote.xmark} | I don't have permissions to manage {registration_channel.mention}.",
                ephemeral=True,
            )

        if not self.channel_perms(slotlist_channel):
            return await interaction.followup.send(
                f"{emote.xmark} | I don't have permissions to manage {slotlist_channel.mention}.",
                ephemeral=True,
            )

        if await Scrim.filter(registration_channel_id=registration_channel.id).exists():
            return await interaction.followup.send(
                f"{emote.xmark} | A scrim already exists in {registration_channel.mention}.",
                ephemeral=True,
            )

        if not interaction.guild.me.guild_permissions.manage_roles:
            return await interaction.followup.send(
                f"{emote.xmark} | I don't have permissions to manage roles.",
                ephemeral=True,
            )

        if success_role.managed:
            return await interaction.followup.send(
                f"{emote.xmark} | I can't give a managed role to users.",
                ephemeral=True,
            )

        if success_role >= interaction.guild.me.top_role:
            return await interaction.followup.send(
                f"{emote.xmark} | I can't set a success role ({success_role.mention}) higher than my top role ({interaction.guild.me.top_role.mention}).",
                ephemeral=True,
            )

        if success_role >= interaction.user.top_role:
            return await interaction.followup.send(
                f"{emote.xmark} | You can't set a success role ({success_role.mention}) higher than your top role ({interaction.user.top_role.mention}).",
                ephemeral=True,
            )

        if self.role_perms(success_role):
            return await interaction.followup.send(
                f"{emote.xmark} | {success_role.mention} has dangerous permissions.",
                ephemeral=True,
            )

        parsed = await self.parse_datetime(interaction, open_time)
        if not parsed:
            return

        autoclean_time = self.bot.current_time.replace(
            hour=randint(3, 6), minute=randint(1, 60), second=0, microsecond=0
        ) + timedelta(days=1)

        scrim = Scrim(
            registration_channel_id=registration_channel.id,
            slotlist_channel_id=slotlist_channel.id,
            role_id=success_role.id,
            required_mentions=required_mentions,
            total_slots=total_slots,
            open_time=parsed,
            host_id=interaction.user.id,
            autoclean_time=autoclean_time,
            guild_id=interaction.guild.id,
        )
        try:
            await scrim.setup_logs()
        except Exception as e:
            return await interaction.followup.send(
                f"### {emote.xmark} An error occured! \n{e}",
                ephemeral=True,
            )
        await scrim.save()
        await self.bot.reminders.create_timer(scrim.open_time, "scrim_open", scrim_id=scrim.id)
        await self.bot.reminders.create_timer(scrim.autoclean_time, "autoclean", scrim_id=scrim.id)

        e = discord.Embed(
            color=discord.Color.green(),
            url=self.bot.config.SERVER_LINK,
            title="Scrim created successfully!",
            description=(
                f"**Registration Channel:** {registration_channel.mention}\n"
                f"**Slotlist Channel:** {slotlist_channel.mention}\n"
                f"**Success Role:** {success_role.mention}\n"
                f"**Required Mentions:** `{required_mentions}`\n"
                f"**Total Slots:** `{total_slots}`\n"
                f"**Open Time:** {discord_timestamp(parsed,'f')}\n"
                f"**Autoclean Time:** {discord_timestamp(autoclean_time,'f')}\n"
                f"**Host:** {interaction.user.mention}\n"
            ),
        )
        e.set_footer(text="Get more info, using `s` command.")

        await interaction.followup.send(embed=e)

    @app_commands.command()
    @app_commands.describe(
        registration_channel="The channel where the scrim is hosted.",
        slot="The slot you want to reserve. (1 to 30)",
        team_name="The name of team.",
        user="(Optional) The user you want to reserve the slot for.",
        expire_time="(Optional) The time when the reservation will expire.",
    )
    async def reserve(
        self,
        interaction: discord.Interaction,
        registration_channel: discord.TextChannel,
        slot: app_commands.Range[int, 1, 30],
        team_name: str,
        user: discord.User = None,
        expire_time: str = None,
    ):
        """Reserve slot in any scrim."""
        await interaction.response.defer(thinking=True, ephemeral=True)

        scrim = await Scrim.get_or_none(registration_channel_id=registration_channel.id)
        if not scrim:
            return await interaction.followup.send(
                embed=discord.Embed(
                    color=discord.Color.red(), description=f"No Scrim found in {registration_channel.mention}."
                )
            )

        expiry = None
        if expire_time:
            expiry = await self.parse_datetime(interaction, expire_time)
            if not expiry:
                return

        await self.reserve_slot(
            scrim=scrim,
            num=slot,
            team_name=team_name,
            user_id=getattr(user, "id", None),
            expires=expiry,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                color=discord.Color.green(),
                description=(
                    f"`Slot {slot}` has been reserved for `{team_name}` in {scrim}. "
                    f"[Time: {'`Lifetime`' if not expiry else discord_timestamp(expiry)}] "
                ),
            )
        )

        other_scrims = await Scrim.filter(
            registration_channel_id__not=registration_channel.id, guild_id=interaction.guild_id
        )

        if not other_scrims:
            return

        prompt = Prompt(interaction.user.id)
        m = await interaction.followup.send("`Do you want to reserve this slot in other scrims as well?`", view=prompt)
        await prompt.wait()

        await m.delete(delay=0)
        if not prompt.value:
            return

        scrims = await self.show_scrims_selector(
            interaction, other_scrims, multi=True, placeholder="Select the scrim you want to reserve slot in."
        )
        if not scrims:
            return

        for scrim in scrims:
            await self.reserve_slot(
                scrim=scrim,
                num=slot,
                team_name=team_name,
                user_id=getattr(user, "id", None),
                expires=expiry,
            )
        await interaction.followup.send(
            embed=discord.Embed(
                color=discord.Color.green(), description=f"`Slot {slot}` reserved successfully for all selected scrims."
            )
        )

    @app_commands.command()
    @app_commands.describe(user="The user you want to unban from scrims.", reason="The reason for unbanning the user.")
    async def unban(self, interaction: discord.Interaction, user: discord.User, reason: str = None):
        """Unban any user from scrims."""
        if not await self.can_use_command(interaction):
            return
        reason = reason or "No reason given."

        # fetching scrims where given user is banned
        query = """
            (SELECT *
		        FROM
			    (SELECT SCRIMS.ID AS SCRIM_ID,
					*
				FROM PUBLIC."sm.scrims" AS SCRIMS
				FULL OUTER JOIN
					(SELECT ID AS BANNED_SLOT_ID,
							*
						FROM PUBLIC."sm.scrims_sm.banned_teams" AS BANNED_SLOT
						INNER JOIN PUBLIC."sm.banned_teams" AS SLOTS ON SLOTS.ID = BANNED_SLOT.BANNEDTEAM_ID) AS BANNED_SLOT ON SCRIMS.ID = BANNED_SLOT."sm.scrims_id"
				WHERE (SCRIMS.GUILD_ID = $1 
										AND BANNED_SLOT."sm.scrims_id" IS NOT NULL)) AS SM
		    WHERE USER_ID = $2)        
            """

        records: T.List[T.Any] = await self.bot.db.fetch(query, interaction.guild_id, user.id)
        if not records:
            return await interaction.response.send_message(f"{user.mention} is not banned from any scrim in this server.")

        await interaction.response.defer(thinking=True, ephemeral=True)

        scrims: T.List[Scrim] = []
        for record in records:
            scrim_id = record["scrim_id"]
            record = dict(record)
            record.pop("id")

            scrims.append(Scrim(id=scrim_id, **record))

        scrims = await Scrim.show_selector(await Context.from_interaction(interaction), scrims)
        if not scrims:
            return

        scrims = [scrims] if isinstance(scrims, Scrim) else scrims

        for scrim in scrims:
            scrim = await Scrim.get_or_none(pk=scrim.id)
            if scrim:
                r = await scrim.banned_teams.filter(user_id=user.id).first()
                if r:
                    await r.delete()

        await interaction.followup.send(
            f"{emote.check} | {user.mention} has been unbanned from `{plural(scrims):scrim|scrims}`.",
            ephemeral=True,
        )

        banlog = await BanLog.get_or_none(guild_id=interaction.guild_id)
        if banlog:
            await banlog.log_unban(user.id, interaction.user, scrims, f"```{reason}```")

    @app_commands.command()
    @app_commands.describe(user="The user whose slots you want to see.")
    async def slotinfo(self, interaction: discord.Interaction, user: discord.Member):
        """Get info about all the slots a user has."""

        if not await self.can_use_command(interaction):
            return

        await interaction.response.defer(thinking=True)

        # I hope one day these ORMs will be able to do this
        query = """
        
        	(SELECT *
		FROM
			(SELECT SCRIMS.ID AS SCRIM_ID,
					*
				FROM PUBLIC."sm.scrims" AS SCRIMS
				FULL OUTER JOIN
					(SELECT ID AS ASSIGNED_SLOT_ID,
							*
						FROM PUBLIC."sm.scrims_sm.assigned_slots" AS ASSIGNED_SLOT
						INNER JOIN PUBLIC."sm.assigned_slots" AS SLOTS ON SLOTS.ID = ASSIGNED_SLOT.ASSIGNEDSLOT_ID) AS ASSIGNED_SLOT ON SCRIMS.ID = ASSIGNED_SLOT."sm.scrims_id"
				WHERE (SCRIMS.GUILD_ID = $1
											AND ASSIGNED_SLOT."sm.scrims_id" IS NOT NULL)) AS SM
		WHERE USER_ID = $2)

        
        """

        records: T.List[T.Any] = await self.bot.db.fetch(query, interaction.guild_id, user.id)
        if not records:
            embed = discord.Embed(
                color=discord.Color.red(),
                description=f"{user.mention} doesn't have any slot in any scrim of this server.",
            )
            return await interaction.followup.send(embed=embed)

        embed = discord.Embed(color=self.bot.color)
        embed.set_author(name=f"{user}'s slots", icon_url=user.display_avatar.url)
        embed.description = ""
        for idx, record in enumerate(records, start=1):
            embed.description += (
                f"`[{idx:02}] ` [**{record['team_name']}**]({record['jump_url']}) - <#{record['registration_channel_id']}>\n"
                "Team: {0}\n\n".format(", ".join([f"<@{member}>" for member in record["members"]]))
            )

        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)
