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

        super().__init__(options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


async def prompt_slot_selection(slots: List[AssignedSlot], placeholder: str):
    first, rest = slots[:25], slots[25:]

    _view = discord.ui.View(timeout=60)
    _view.custom_id = None

    _view.add_item(ScrimSlotSelector(first, placeholder=placeholder))

    if rest:
        _view.add_item(ScrimSlotSelector(rest, placeholder=placeholder))

    return _view
