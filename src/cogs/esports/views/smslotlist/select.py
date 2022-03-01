from __future__ import annotations


from typing import List

from models import AssignedSlot
import discord
import config

from utils import truncate_string as ts, emote, keycap_digit as kd


class ScrimSlotSelector(discord.ui.Select):
    def __init__(self, slots: List[AssignedSlot], *, placeholder: str, multiple=False):

        _options = []
        for slot in slots:

            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.num}", description=ts(slot.team_name, 22), emoji=emote.TextChannel, value=slot.id
                )
            )

        super().__init__(options=_options, placeholder=placeholder, max_values=len(_options) if multiple else 1)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0] if not self.max_values > 1 else interaction.data["values"]


async def prompt_slot_selection(slots: List[AssignedSlot], placeholder: str, multiple: bool = False):
    first, rest = slots[:25], slots[25:]

    _view = discord.ui.View(timeout=60)
    _view.custom_id = None

    _view.add_item(ScrimSlotSelector(first, placeholder=placeholder, multiple=multiple))

    if rest:
        _view.add_item(ScrimSlotSelector(rest, placeholder=placeholder, multiple=multiple))

    return _view


class BanOptions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value: str = None

    def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3, title="Ban karne ka style choose karo :)", url=config.SERVER_LINK)
        _e.description = (
            f"{kd(1)} - Ban Team leader from this scrim.\n\n"
            f"{kd(2)} - Ban whole team from this scrim.\n\n"
            f"{kd(3)} - Ban Team leader from all scrims.\n\n"
            f"{kd(4)} - Ban whole team from all scrims."
        )
        return _e

    @discord.ui.button(emoji=kd(1))
    async def on_one(self, button: discord.Button, interaction: discord.Interaction):
        self.value = "1"
        self.stop()

    @discord.ui.button(emoji=kd(2))
    async def on_two(self, button: discord.Button, interaction: discord.Interaction):
        self.value = "2"
        self.stop()

    @discord.ui.button(emoji=kd(3))
    async def on_three(self, button: discord.Button, interaction: discord.Interaction):
        self.value = "3"
        self.stop()

    @discord.ui.button(emoji=kd(4))
    async def on_four(self, button: discord.Button, interaction: discord.Interaction):
        self.value = "4"
        self.stop()
