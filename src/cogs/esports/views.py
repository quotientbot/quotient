from utils import emote, BaseSelector
from datetime import datetime
from constants import IST
from typing import List, NamedTuple
from models import Scrim, AssignedSlot
import discord

__all__ = ("ScrimSelector", "SlotManagerView")


class ScrimSlot(NamedTuple):
    num: int
    scrim: Scrim


class CancelSlot(NamedTuple):
    obj: AssignedSlot
    scrim: Scrim


class ScrimSelector(discord.ui.Select):
    def __init__(self, placeholder: str, scrims: List[Scrim]):

        _options = []
        for scrim in scrims:
            _options.append(
                discord.SelectOption(
                    label=scrim.name,
                    value=scrim.id,
                    description=f"{scrim.registration_channel} (ScrimID: {scrim.id})",
                    emoji=emote.category,
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class ClaimSlotSelector(discord.ui.Select):
    def __init__(self, placeholder: str, slots: List[ScrimSlot]):

        _options = []
        for slot in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.num} ─ {getattr(slot.scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{slot.scrim.name} (ID: {slot.scrim.id})",
                    value=f"{slot.scrim.id} {slot.num}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class CancelSlotSelector(discord.ui.Select):
    def __init__(self, placeholder: str, slots: List[CancelSlot]):

        _options = []
        for slot in slots:
            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.obj.num} ─ {getattr(slot.scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{slot.obj.team_name} (ID: {slot.scrim.id})",
                    value=slot.obj.id,
                    emoji="📇",
                )
            )

        super().__init__(placeholder=placeholder, options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class SlotManagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_buttons(self):
        ...

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="cancel-slot", label="Cancel Your Slot")
    async def cancel_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        _slots = []
        async for scrim in Scrim.filter(guild_id=interaction.guild_id):
            async for slot in scrim.assigned_slots.filter(user_id=interaction.user.id):
                _slots.append(CancelSlot(slot, scrim))

        if not _slots:
            return await interaction.followup.send("You haven't registred in any scrim today.", ephemeral=True)

        if len(_slots) > 25:
            return await interaction.followup.send(
                "You have more than 25 slots. Kindly contact moderators.", ephemeral=True
            )

        cancel_view = BaseSelector(interaction.user.id, CancelSlotSelector, placeholder="select a slot", slots=_slots)
        await interaction.followup.send("Choose a slot to cancel", view=cancel_view, ephemeral=True)
        await cancel_view.wait()
        print(cancel_view.custom_id)

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="claim-slot", label="Claim Slot")
    async def claim_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        _time = datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)
        records = Scrim.filter(guild_id=interaction.guild_id, closed_at__gte=_time, available_slots__not=[])

        _slots = []
        async for record in records:
            for slot in record.available_slots:
                _slots.append(ScrimSlot(slot, record))

        if not _slots:
            return await interaction.followup.send(
                "There is no slot available right now. Please try again later.", ephemeral=True
            )

        if len(_slots) > 25:
            return await interaction.followup.send(
                "More than 25 slots are available. Please contact moderators.", ephemeral=True
            )

        claim_view = BaseSelector(interaction.user.id, ClaimSlotSelector, placeholder="select slot", slots=_slots)
        await interaction.followup.send("Choose a slot to claim", view=claim_view, ephemeral=True)
        await claim_view.wait()
        print(claim_view.custom_id)
