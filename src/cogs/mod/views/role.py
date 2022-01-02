from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from utils import emote

import discord
from core import Context
from contextlib import suppress


class RoleRevertButton(discord.ui.Button):
    def __init__(self, ctx: Context, *, role: discord.Role, members: typing.List[discord.Member], take_role=True):
        super().__init__()

        self.emoji = emote.exit
        self.label = "Take Back" if take_role else "Give Back"
        self.custom_id = "role_revert_action_button"

        self.ctx = ctx
        self.role = role
        self.members = members
        self.take_role = take_role

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.view.on_timeout()

        for _ in self.members:
            with suppress(discord.HTTPException):
                await _.remove_roles(self.role) if self.take_role else await _.add_roles(self.role)

        return await self.ctx.success("Succesfully reverted the action.")


class RoleCancelButton(discord.ui.Button):
    def __init__(self, ctx: Context, *, role: discord.Role, members: typing.List[discord.Member]):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.role = role
        self.members = members
