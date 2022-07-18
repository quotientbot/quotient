from __future__ import annotations

import typing as T

from models import Scrim, ScrimsSlotReminder
import discord
from ..public import ScrimsSlotmPublicView
from cogs.esports.views.scrims import ScrimSelectorView

from utils import plural

__all__ = ("ScrimsRemind",)


class ScrimsRemind(discord.ui.Button):
    view: ScrimsSlotmPublicView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction) -> T.Any:
        await interaction.response.defer(thinking=True, ephemeral=True)

        if not await self.view.bot.is_premium_guild(interaction.guild_id):
            return await interaction.followup.send(
                "Cancel Reminder feature is only available for premium servers.\n\n"
                f"*This server needs to purchase [Quotient Premium]({self.view.bot.prime_link}) to use this feature.*",
                ephemeral=True,
            )

        scrims = await Scrim.filter(
            pk__in=self.view.record.scrim_ids,
            closed_at__gt=self.view.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
            match_time__gt=self.view.bot.current_time,
            opened_at__isnull=True,
            available_slots=[],
        ).order_by("open_time")

        for scrim in await self.banned_from(interaction.user.id):
            for _ in scrims:
                if _.id == scrim["scrim_id"]:
                    scrims.remove(_)

        for scrim in await self.already_reminder_of(interaction.user.id):
            for _ in scrims:
                if _.id == scrim["scrim_id"]:
                    scrims.remove(_)

        if not self.view.record.multiple_slots:
            for slot in await self.view.record.user_slots(interaction.user.id):
                for _ in scrims:
                    if _.id == slot["scrim_id"]:
                        scrims.remove(_)

        if not scrims:
            return await interaction.followup.send("You can't set reminder in any scrim at this time.", ephemeral=True)

        _view = ScrimSelectorView(interaction.user, scrims[:25], placeholder="Select scrims to add slot reminder")
        await interaction.followup.send(
            "Select 1 or multiple scrims to set reminder\n\n*By selecting scrims, you confirm that Quotient can "
            "DM you when any slot is available of the selected scrims.*",
            view=_view,
            ephemeral=True,
        )
        await _view.wait()
        if not _view.custom_id:
            return

        scrims = await Scrim.filter(pk__in=_view.custom_id)

        for _ in scrims:
            _r = await ScrimsSlotReminder.create(user_id=interaction.user.id)
            await _.slot_reminders.add(_r)

        _e = discord.Embed(
            color=0x00FFB3, description=f"Successfully created reminder for {plural(scrims):scrim|scrims}."
        )

        await interaction.followup.send(embed=_e, ephemeral=True)

    async def banned_from(self, user_id: int) -> T.List[int]:
        # now, can tortoise do this? - no way
        query = """
        (SELECT *
		    FROM
			(SELECT SCRIMS.ID AS SCRIM_ID,
					*
				FROM PUBLIC."sm.scrims" AS SCRIMS
				FULL OUTER JOIN
					(SELECT ID AS ASSIGNED_SLOT_ID,
							*
						FROM PUBLIC."sm.scrims_sm.banned_teams" AS SCRIM_SLOT
						INNER JOIN PUBLIC."sm.banned_teams" AS SLOTS ON SLOTS.ID = SCRIM_SLOT.BANNEDTEAM_ID) AS SCRIM_SLOT ON SCRIMS.ID = SCRIM_SLOT."sm.scrims_id"
				WHERE (SCRIMS.ID = ANY ($1)
										AND SCRIM_SLOT."sm.scrims_id" IS NOT NULL)) AS SM
		WHERE USER_ID = $2)        
        """

        return await self.view.bot.db.fetch(query, self.view.record.scrim_ids, user_id)

    async def already_reminder_of(self, user_id: int) -> T.List[int]:
        query = """
        (SELECT *
		    FROM
			    (SELECT SCRIMS.ID AS SCRIM_ID,
					*
				    FROM PUBLIC."sm.scrims" AS SCRIMS
				    FULL OUTER JOIN
					    (SELECT ID AS REMINDER_SLOT_ID,
							*
						    FROM PUBLIC."sm.scrims_scrims_slot_reminders" AS REMINDER_SLOT
						    INNER JOIN PUBLIC."scrims_slot_reminders" AS SLOTS ON SLOTS.ID = REMINDER_SLOT.SCRIMSSLOTREMINDER_ID) AS REMINDER_SLOT ON SCRIMS.ID = REMINDER_SLOT."sm.scrims_id"
				    WHERE (SCRIMS.ID = ANY ($1)
											AND REMINDER_SLOT."sm.scrims_id" IS NOT NULL)) AS SM
		WHERE USER_ID = $2)
        """
        return await self.view.bot.db.fetch(query, self.view.record.scrim_ids, user_id)
