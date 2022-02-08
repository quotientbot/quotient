from __future__ import annotations

from ...views.base import EsportsBaseView

from core import Context
from models import Tourney

from ._buttons import *
from string import ascii_uppercase
from ..ssmod._buttons import DiscardButton


class TourneySetupWizard(EsportsBaseView):
    record: Tourney

    def __init__(self, ctx: Context):
        super().__init__(ctx)

        self.ctx = ctx
        self.record = None

        self.add_item(RegChannel(ctx, "a"))
        self.add_item(ConfirmChannel(ctx, "b"))
        self.add_item(SetRole(ctx, "c"))
        self.add_item(SetMentions(ctx, "d"))
        self.add_item(SetSlots(ctx, "e"))
        self.add_item(SetEmojis(ctx,"f"))
        self.add_item(DiscardButton())
        self.add_item(SaveTourney(ctx))

    def initial_message(self):
        if not self.record:
            self.record = Tourney(guild_id=self.ctx.guild.id)

        fields = {
            "Registration Channel": getattr(self.record.registration_channel, "mention", "`Not-Set`"),
            "Confirm Channel": getattr(self.record.confirm_channel, "mention", "`Not-Set`"),
            "Success Role": getattr(self.record.role, "mention", "`Not-Set`"),
            "Mentions": f"`{self.record.required_mentions}`",
            "Slots": f"`{self.record.total_slots or '`Not-Set`'}`",
            f"Reactions {self.bot.config.PRIME_EMOJI}": f"{self.record.check_emoji},{self.record.cross_emoji}",
        }

        _e = discord.Embed(color=0x00FFB3, title="Enter details & Press Save", url=self.bot.config.SERVER_LINK)

        for idx, (name, value) in enumerate(fields.items()):
            _e.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )

        return _e

    async def refresh_view(self):
        _e = self.initial_message()

        if all(
            (
                self.record.registration_channel_id,
                self.record.role_id,
                self.record.confirm_channel_id,
                self.record.required_mentions,
                self.record.total_slots,
            )
        ):
            self.children[-1].disabled = False

        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()
