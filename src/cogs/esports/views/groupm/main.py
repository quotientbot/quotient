from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import discord
from ..base import EsportsBaseView
from core import Context

__all__ = ("TourneyGroupManager",)


class TourneyGroupManager(EsportsBaseView):
    def __init__(self, ctx: Context, **kwargs):
        super().__init__(ctx, **kwargs)

    @property
    def initial_message(self):
        _e = discord.Embed()
        _e.description = (
            "Use `qcreateroles` command to create group roles for this tournament`\n",
            "Don't create channels to send group list, let Quotient do that for you :)\n",
        )
        return _e

    @discord.ui.button(label="")
    async def set_category(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="")
    async def set_rolename(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="")
    async def slotlist_start(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="")
    async def group_size(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="")
    async def ping_group_role(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="")
    async def send_grouplist(self, button: discord.Button, interaction: discord.Interaction):
        ...
