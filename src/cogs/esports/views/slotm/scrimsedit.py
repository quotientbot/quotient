from __future__ import annotations

from ...views.base import EsportsBaseView
from models import ScrimsSlotManager, Scrim
from core import Context

from utils import emote
import discord


from cogs.esports.views.scrims import ScrimSelectorView

__all__ = ("SlotmScrimsEditor",)


class SlotmScrimsEditor(EsportsBaseView):
    def __init__(self, ctx: Context, record: ScrimsSlotManager):
        super().__init__(ctx, timeout=100, title="Slot-M Editor")

        self.ctx = ctx
        self.record = record

    def initial_embed(self) -> discord.Embed:
        _e = discord.Embed(color=0x00FFB3)
        _e.description = (
            "Do you want to add scrims of remove scrims from this slot-m?\n\n"
            f"Current scrims: {', '.join(f'`{str(_)}`' for _ in self.record.scrim_ids)}"
        )

        return _e

    @discord.ui.button(custom_id="slotm_scrims_add", emoji=emote.add)
    async def add_new_scrims(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.record.refresh_from_db()

        scrims = await self.record.available_scrims(self.ctx.guild)
        if not scrims:
            return await self.ctx.error("All scrims are already added to this or another slot-m.", 3)

        scrims = scrims[:25]
        _view = ScrimSelectorView(interaction.user, scrims, placeholder="Select scrims to add to this slot-manager ...")
        await interaction.followup.send("Choose the scrims you want to add to this slotm.", view=_view, ephemeral=True)

        await _view.wait()
        if _view.custom_id:
            _q = "UPDATE slot_manager SET scrim_ids = scrim_ids || $1 WHERE id = $2"
            await self.ctx.bot.db.execute(_q, [int(i) for i in _view.custom_id], self.record.id)
            await self.record.refresh_public_message()
            await self.ctx.success("Successfully added new scrims.", 3)

    @discord.ui.button(custom_id="slotm_scrims_remove", emoji=emote.remove)
    async def remove_scrims(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        await self.record.refresh_from_db()
        if not self.record.scrim_ids:
            return await self.ctx.error("There are no scrims added to this slot-m.", 3)

        scrims = await Scrim.filter(pk__in=self.record.scrim_ids).limit(25)
        _view = ScrimSelectorView(
            interaction.user, scrims, placeholder="Select scrims to remove from this slot-manager ..."
        )

        await interaction.followup.send(
            "Choose the scrims you want to remove from this slotm.", view=_view, ephemeral=True
        )
        await _view.wait()
        if _view.custom_id:
            _q = "UPDATE slot_manager SET scrim_ids = $1 WHERE id = $2"
            await self.ctx.bot.db.execute(
                _q, [_ for _ in self.record.scrim_ids if not str(_) in _view.custom_id], self.record.id
            )
            await self.record.refresh_public_message()
            await self.ctx.success("Successfully removed selected scrims.", 3)
