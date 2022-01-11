from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView
from core import Context

from models.esports.slotm import ScrimsSlotManager
from cogs.esports.views.scrims import ScrimSelectorView
import discord

from models import Scrim
from utils import emote


__all__ = ("ScrimsSlotManagerSetup",)


class ScrimsSlotManagerSetup(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=60, title="Scrims Slot Manager")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    async def initial_message(guild: discord.Guild):
        records = await ScrimsSlotManager.filter(guild_id=guild.id)
        _to_show = [_.__str__() for _ in records]

        _sm = "\n".join(_to_show) if _to_show else "```No scrims slot managers found.```"

        _e = discord.Embed(color=0x00FFB3, title=f"Scrims Slot-Manager Setup")

        _e.description = f"Current slot-manager channels:\n{_sm}"
        return _e

    @discord.ui.button(label="Add Channel", custom_id="scrims_slotm_addc")
    async def add_channel(self, button: discord.Button, interaction: discord.Interaction):
        available_scrims = await ScrimsSlotManager.available_scrims(self.ctx.guild)
        if not available_scrims:
            return await self.error_embed(
                f"There are no scrims available for a new slotmanager channel.\n\n"
                "If you have other slot-m channel, first remove the scrims from that channel to add them to new slot-m."
            )

        _view = ScrimSelectorView(
            interaction.user, available_scrims, placeholder="Select scrims to add to slot-manager ..."
        )
        await self.ctx.send("Choose 1 or multiple scrims that you want to add to new slot-manager.", view=_view)
        await _view.wait()
        print(_view.custom_id)
        # await Scrim.filter(pk__in=view.custom_id).order_by("id")

    @discord.ui.button(label="Edit Config", custom_id="scrims_slotm_editc")
    async def edit_config(self, button: discord.Button, interaction: discord.Interaction):
        records = await ScrimsSlotManager.filter(guild_id=self.ctx.guild.id)
        if not records:
            return await self.ctx.error(
                "You haven't added any slot-manager channel yet.\n\nClick `Add Channel` to add a new slot-m channel.", 2
            )

    class ScrimsSlotmSelector(discord.ui.Select):
        def __init__(self, records: List[ScrimsSlotManager]):

            _o = []
            for record in records:
                _o.append(
                    discord.SelectOption(
                        label=getattr(record.main_channel, "name", "channel-not-found"),  # type: ignore
                        value=record.id,
                        description=f"Scrims: {', '.join(str(_) for _ in record.scrim_ids)}",
                        emoji=emote.TextChannel,
                    )
                )

            super().__init__(placeholder="Select a slot-manager channel ...", options=_o)
