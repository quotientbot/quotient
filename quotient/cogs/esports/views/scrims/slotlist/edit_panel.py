import discord
from lib import user_input

from quotient.models import Scrim, ScrimAssignedSlot

from ..utility.selectors import prompt_scrims_slot_selector


class NewTeamNameModal(discord.ui.Modal, title="New Team Name"):
    new_team_name = discord.ui.TextInput(label="Enter new teamname:", min_length=3, max_length=25)

    async def on_submit(self, inter: discord.Interaction) -> None:
        await inter.response.defer()


class ScrimSlotlistEditPanel(discord.ui.View):
    message: discord.Message

    def __init__(self, scrim: Scrim):
        super().__init__(timeout=50)

        self.scrim = scrim
        self.bot = scrim.bot
        self.slotlist_msg = self.scrim.registration_channel.get_partial_message(self.scrim.slotlist_message_id)

    async def on_timeout(self) -> None:
        if not hasattr(self, "message"):
            return

        for c in self.children:
            if isinstance(c, discord.ui.Button):
                c.disabled = True
                c.style = discord.ButtonStyle.grey

        try:
            return await self.message.edit(view=self)
        except discord.NotFound:
            pass

    def initial_embed(self) -> discord.Embed:
        _e = discord.Embed(color=0x00FFB3, description="Choose an option below to edit the slotlist.")
        return _e

    @discord.ui.button(style=discord.ButtonStyle.success, label="Replace / Change Team", custom_id="smslot_change_team")
    async def change_team_name(self, inter: discord.Interaction, button: discord.Button):
        modal = NewTeamNameModal(timeout=30)
        await inter.response.send_modal(modal)

        await modal.wait()
        if not modal.new_team_name.value:
            return

        assigned_slots = list(self.scrim.assigned_slots)

        if not assigned_slots:
            return await self.message.edit(content="No slot available to replace.", embed=None, view=None)

        await self.message.delete(delay=0)
        slot = await prompt_scrims_slot_selector(
            inter, assigned_slots, "Select the slot to change team name...", placeholder="Click me to pick a slot"
        )
        if not (slot := slot[0]):
            return

        new_team_leader = await user_input(
            inter,
            f"Please select the new team leader for `Team {modal.new_team_name.value}`:",
            placeholder="Select a user...",
            multiple=False,
        )
        if not new_team_leader:
            return

        await ScrimAssignedSlot.filter(pk=slot.id).update(
            team_name=modal.new_team_name.value, leader_id=new_team_leader[0].id, members=[new_team_leader[0].id]
        )

        await inter.followup.send(embed=self.bot.success_embed("Slotlist updated successfully."), ephemeral=True)
        return await self.scrim.refresh_slotlist_message()

    @discord.ui.button(style=discord.ButtonStyle.red, label="Remove Team", custom_id="smslot_remove_team")
    async def remove_team_name(self, inter: discord.Interaction, button: discord.Button):
        await inter.response.defer()

        assigned_slots = list(self.scrim.assigned_slots)

        if not assigned_slots:
            return await self.message.edit(content="No slot available to replace.", embed=None, view=None)

        await self.message.delete(delay=0)
        slots_to_remove = await prompt_scrims_slot_selector(
            inter,
            assigned_slots,
            "Select the slots you want to remove.",
            placeholder="Click me to pick slots...",
            multiple=True,
        )
        if not slots_to_remove:
            return

        self.scrim.available_slots = sorted(self.scrim.available_slots + [_.num for _ in slots_to_remove])
        await self.scrim.save(update_fields=["available_slots"])
        await ScrimAssignedSlot.filter(pk__in=[_.id for _ in slots_to_remove]).delete()

        await self.scrim.refresh_slotlist_message()

        await inter.followup.send(embed=self.bot.success_embed("Successfully removed selected teams from slotlist."), ephemeral=True)

        await self.scrim.fetch_related("slotm")

        if self.scrim.slotm:
            await self.scrim.slotm.refresh_public_message()

    @discord.ui.button(label="Add Team", custom_id="smslot_add_team", style=discord.ButtonStyle.green)
    async def add_new_team(self, inter: discord.Interaction, button: discord.Button):
        modal = NewTeamNameModal(timeout=30)
        await inter.response.send_modal(modal)

        await modal.wait()
        if not modal.new_team_name.value:
            return

        if not self.scrim.available_slots:
            return await self.message.edit(content="No slots available to add this time.", embed=None, view=None)

        team_members = await user_input(
            inter,
            f"Please select the team members for `Team {modal.new_team_name.value}`: (First user is treated as Leader)",
            placeholder="Select users...",
            multiple=True,
        )
        if not team_members:
            return

        await self.scrim.refresh_from_db(fields=["available_slots"])
        if not self.scrim.available_slots:
            return await self.message.edit(content="No slots available to add this time.", embed=None, view=None)

        slot = await ScrimAssignedSlot.create(
            scrim=self.scrim,
            num=self.scrim.available_slots[0],
            team_name=modal.new_team_name.value,
            leader_id=team_members[0].id,
            members=[_.id for _ in team_members],
        )

        self.scrim.available_slots.remove(slot.num)
        await self.scrim.save(update_fields=["available_slots"])

        await self.scrim.refresh_slotlist_message()

        await inter.followup.send(
            embed=self.bot.success_embed(f"`Team {slot.team_name}` has been added at `Slot {slot.num}`"), ephemeral=True
        )

        await self.scrim.fetch_related("slotm")

        if self.scrim.slotm:
            await self.scrim.slotm.refresh_public_message()
