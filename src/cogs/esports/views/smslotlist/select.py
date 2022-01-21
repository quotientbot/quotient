from __future__ import annotations


from typing import List

from models import AssignedSlot
import discord

from utils import truncate_string as ts, emote


class ScrimSlotSelector(discord.ui.Select):
    def __init__(self, slots: List[AssignedSlot], *, placeholder=str):

        _options = []
        for slot in slots:

            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.num}", description=ts(slot.team_name, 22), emoji=emote.TextChannel, value=slot.id
                )
            )

        super().__init__(timeout=60)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


async def prompt_slot_selection(slots: List[AssignedSlot], placeholder: str):
    ...
