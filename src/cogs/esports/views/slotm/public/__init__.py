from __future__ import annotations

import typing as T

import discord as d

from models import Scrim, ScrimsSlotManager

__all__ = ("ScrimsSlotmPublicView",)


class ScrimsSlotmPublicView(d.ui.View):
    children: T.List[d.ui.Button]

    def __init__(self, record: ScrimsSlotManager):
        super().__init__(timeout=None)

        self.record = record
        self.bot = record.bot
        self.claimable: T.List[Scrim] = []

        from ._cancel import ScrimsCancel
        from ._claim import ScrimsClaim
        from ._idp import IdpTransfer
        from ._reminder import ScrimsRemind

        self.add_item(ScrimsCancel(style=d.ButtonStyle.danger, custom_id="scrims_slot_cancel", label="Cancel Slot"))
        self.add_item(ScrimsClaim(style=d.ButtonStyle.green, custom_id="scrims_slot_claim", label="Claim Slot"))
        self.add_item(ScrimsRemind(label="Remind Me", custom_id="scrims_slot_reminder", emoji="🔔"))
        self.add_item(
            IdpTransfer(label="Transfer IDP Role", custom_id="scrims_transfer_idp_role", style=d.ButtonStyle.green)
        )

        self.bot.loop.create_task(self.__refresh_cache())

    async def on_error(self, interaction: d.Interaction, error: Exception, item: d.ui.Item[T.Any]) -> None:
        if isinstance(error, d.NotFound):
            return
        print("Scrims Slotm Public View Error:", error)

    async def __refresh_cache(self):
        async for scrim in self.record.claimable_slots:
            self.claimable.append(scrim)
