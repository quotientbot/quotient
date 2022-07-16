from __future__ import annotations

from typing import TYPE_CHECKING

from utils.buttons import Prompt

if TYPE_CHECKING:
    from core import Quotient

from string import ascii_uppercase

import discord

from core import Context
from models.esports.slotm import ScrimsSlotManager
from utils import plural
from utils import regional_indicator as ri

from ...views.base import EsportsBaseView
from .scrimsedit import SlotmScrimsEditor

__all__ = ("ScrimsSlotmEditor",)


class ScrimsSlotmEditor(EsportsBaseView):
    def __init__(self, ctx: Context, *, record: ScrimsSlotManager):
        super().__init__(ctx, timeout=30, title="Slot-M Editor")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot
        self.record = record

    def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3, title="Slot-M Editor")

        fields = {
            "Main Channel": getattr(self.record.main_channel, "mention", "Not-Found"),
            "Slot-m Status": f"{'Enabled' if self.record.toggle else 'Disabled'}",
            "Reminders button": f"{'Enabled' if self.record.allow_reminders else 'Disabled'}",
            "Multi Slot-Claim": f"{'Enabled' if self.record.multiple_slots else 'Disabled'}",
            "Scrims": f"{plural(self.record.scrim_ids):scrim|scrims} (`Click to edit`)",
        }

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )
        _e.add_field(name=f"🟥 Delete Slot-M", value=f"`Click to delete`")
        return _e

    async def __update_record(self, **kwargs):
        await ScrimsSlotManager.filter(pk=self.record.pk).update(**kwargs)
        await self.__refresh_embed()
        await self.record.refresh_public_message()

    async def __refresh_embed(self):
        await self.record.refresh_from_db()
        embed = self.initial_embed()

        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(custom_id="edit_main_slotm_channel", emoji=ri("A"))
    async def edit_main_slotm_channel(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        return await interaction.followup.send("Main Channel can't be edited. Sorry 🥲", ephemeral=True)

    @discord.ui.button(custom_id="edit_slotm_status", emoji=ri("B"))
    async def edit_slotm_status(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await self.__update_record(toggle=not self.record.toggle)

    @discord.ui.button(custom_id="edit_slotm_reminders", emoji=ri("C"))
    async def edit_slotm_reminders(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await self.__update_record(allow_reminders=not self.record.allow_reminders)

    @discord.ui.button(custom_id="edit_slotm_multi_claim", emoji=ri("D"))
    async def edit_slotm_multi_claim(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()
        await self.__update_record(multiple_slots=not self.record.multiple_slots)

    @discord.ui.button(custom_id="edit_slotm_scrims", emoji=ri("E"))
    async def edit_slotm_scrims(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

        _view = SlotmScrimsEditor(self.ctx, self.record)
        await interaction.followup.send(embed=_view.initial_embed(), view=_view, ephemeral=True)
        await self.on_timeout()

    @discord.ui.button(custom_id="delete_slotm", label="Delete Slot-Manager", style=discord.ButtonStyle.red)
    async def delete_slotm(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.defer()

        prompt = Prompt(self.ctx.author.id)
        await interaction.followup.send("Are you sure you want to delete this Slot-Manager?", view=prompt, ephemeral=True)
        await prompt.wait()
        if not prompt.value:
            return await self.ctx.simple("Alright, Aborting.", 2)

        await self.record.full_delete()
        await self.ctx.success("Slot-M Deleted.", 2)
        await self.on_timeout()
