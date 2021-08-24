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


class SlotSelector(discord.ui.Select):
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


class SlotManagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_buttons(self):
        ...

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="cancel-slot", label="Cancel Your Slot")
    async def cancel_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        myview = BaseSelector(
            interaction.user.id,
            ScrimSelector,
            placeholder="select scrim",
            scrims=await Scrim.filter(guild_id=interaction.guild_id),
        )
        await interaction.followup.send("select something", view=myview, ephemeral=True)
        await myview.wait()
        print(myview.custom_id)

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id="claim-slot", label="Claim Slot")
    async def claim_slot(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        _time = datetime.now(tz=IST).replace(hour=0, minute=0, second=0, microsecond=0)
        records = await Scrim.filter(guild_id=interaction.guild_id, closed_at__gte=_time, available_slots__not=[])

        if not records:
            return await interaction.followup.send(
                "There is no slot available right now. Please try again later.", ephemeral=True
            )

        if len(records) > 25:
            return await interaction.followup.send("Maximum slot value reached.", ephemeral=True)

        _slots = []
        for record in records:
            for slot in record.available_slots:
                _slots.append(ScrimSlot(slot, record))

        claim_view = BaseSelector(interaction.user.id, SlotSelector, placeholder="select slot", slots=_slots)
        await interaction.followup.send("Choose a slot to claim", view=claim_view, ephemeral=True)
        await claim_view.wait()
        print(claim_view.custom_id)
