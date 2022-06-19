from __future__ import annotations

from core import Context
import discord

from models import Scrim
from ._base import ScrimsView
from utils import inputs, emote

__all__ = ("ManageSlotlist",)

#!TODO:  make format btn


class ManageSlotlist(discord.ui.Select):
    view: ScrimsView

    def __init__(self, ctx: Context, scrim: Scrim):
        super().__init__(
            placeholder="Select an option to manage slotlist.",
            options=[
                discord.SelectOption(
                    label="Repost Slotlist",
                    emoji="<:re:980844295303098438>",
                    description="Respost slotlist to a channel",
                    value="repost",
                ),
                discord.SelectOption(
                    label="Change Design",
                    description="Design slotlist of any scrim.",
                    emoji="<:settings:980844348159688706>",
                    value="format",
                ),
                discord.SelectOption(
                    label="Go Back",
                    description="Move back to Main Menu",
                    emoji=emote.exit,
                    value="back",
                ),
            ],
        )

        self.ctx = ctx
        self.record = scrim

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.stop()

        if (selected := self.values[0]) == "repost":
            m = await self.ctx.simple("Mention the channel to send slotlist.")
            channel = await inputs.channel_input(self.ctx, delete_after=True)
            await self.ctx.safe_delete(m)

            if not await self.record.teams_registered.count():
                return await self.ctx.error("No registrations found in {0}.".format(self.record), 5)

            m = await self.record.send_slotlist(channel)
            await self.ctx.success("Slotlist sent! [Click to Jump]({0})".format(m.jump_url), 5)

            from .main import ScrimsMain

            self.view.stop()
            v = ScrimsMain(self.ctx)
            v.message = await self.view.message.edit(content="", embed=await v.initial_embed(), view=v)

        elif selected == "format":
            ...

        elif selected == "back":
            from .main import ScrimsMain

            self.view.stop()
            v = ScrimsMain(self.ctx)
            v.message = await self.view.message.edit(content="", embed=await v.initial_embed(), view=v)
