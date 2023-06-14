from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from core import Context
from discord import app_commands
from discord.ext import commands
from models import BanLog, Scrim
from utils import emote, plural

__all__ = ("ScrimsSlash",)


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

    @app_commands.command()
    @app_commands.describe(user="The user you want to ban from scrims.", reason="The reason for unbanning the user.")
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
