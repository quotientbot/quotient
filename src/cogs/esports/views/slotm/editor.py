from __future__ import annotations
from _typeshed import OpenTextMode

from typing import TYPE_CHECKING

from utils.buttons import Prompt


if TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView

from core import Context
from models.esports.slotm import ScrimsSlotManager

from utils import plural, regional_indicator as ri

from string import ascii_uppercase
import discord


class ScrimsSlotmEditor(EsportsBaseView):
    def __init__(self, ctx: Context, *, record: ScrimsSlotManager):
        super().__init__(ctx, timeout=60, title="Slot-M Editor")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot
        self.record = record

    @classmethod
    async def initial_embed(cls: ScrimsSlotmEditor):
        _e = discord.Embed(color=0x00FFB3, title="Slot-M Editor")

        fields = {
            "Main Channel": getattr(cls.record.main_channel, "mention", "Not-Found"),
            "Status": f"{'Enabled' if cls.record.toggle else 'Disabled'}",
            "Allow Reminders": f"{'Enabled' if cls.record.allow_reminders else 'Disabled'}",
            "Allow Multi-Claim": f"{'Enabled' if cls.record.multiple_slots else 'Disabled'}",
            "Scrims": f"{plural(cls.record.scrim_ids):scrim|scrims} (`Click to edit`)",
        }
        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )
        return _e

    async def __update_record(self, **kwargs):
        await ScrimsSlotManager.filter(pk=self.record.pk).update(**kwargs)
        await self.__refresh_embed()

    async def __refresh_embed(self):
        await self.record.refresh_from_db()
        embed = await self.initial_embed()

        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(custom_id="edit_main_slotm_channel", emoji=ri("A"))
    async def edit_main_slotm_channel(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(custom_id="edit_slotm_status", emoji=ri("B"))
    async def edit_slotm_status(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.__update_record(toggle=not self.record.toggle)

    @discord.ui.button(custom_id="edit_slotm_reminders", emoji=ri("C"))
    async def edit_slotm_reminders(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.__update_record(allow_reminders=not self.record.allow_reminders)

    @discord.ui.button(custom_id="edit_slotm_multi_claim", emoji=ri("D"))
    async def edit_slotm_multi_claim(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.__update_record(multiple_slots=not self.record.multiple_slots)

    @discord.ui.button(custom_id="edit_slotm_scrims", emoji=ri("E"))
    async def edit_slotm_scrims(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(custom_id="delete_slotm", label="Delete Slot-M", style=discord.ButtonStyle.red)
    async def delete_slotm(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        prompt = Prompt(self.ctx.author.id)
        await interaction.followup.send("Are you sure you want to delete this Slot-Manager?", view=prompt)
        await prompt.wait()
        if not prompt.value:
            return await self.ctx.simple("Alright, Aborting.", 2)

        await self.record.full_delete()
        return await self.ctx.success("Slot-M Deleted.", 2)
