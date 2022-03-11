from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from ..base import EsportsBaseView
from core import Context

from models import Tourney

from utils import keycap_digit

__all__ = ("TourneyGroupManager",)


class TourneyGroupManager(EsportsBaseView):
    def __init__(self, ctx: Context, **kwargs):
        super().__init__(ctx, **kwargs)

        self.ping_role = True
        self.start_from = 2

    @property
    def initial_embed(self):
        _e = discord.Embed(color=self.ctx.bot.color)
        _e.description = (
            f"Use `create channels & roles` to setup tourney groups.\n"
            "Use `Group List` to post group/slotlist in channels."
        )
        _e.add_field(name=f"{keycap_digit(1)} Slotlist Start from", value=f"`Slot {self.start_from}`")
        _e.add_field(name=f"{keycap_digit(2)} Ping Group Role", value=("`No!`", "`Yes!`")[self.ping_role])
        return _e

    @discord.ui.button(emoji=keycap_digit(1))
    async def slotlist_start(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(emoji=keycap_digit(2))
    async def ping_group_role(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Create Channels & Roles")
    async def create_roles_channels(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Group List", style=discord.ButtonStyle.green)
    async def send_grouplist(self, button: discord.Button, interaction: discord.Interaction):
        ...
