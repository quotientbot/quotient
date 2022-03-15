from __future__ import annotations

import typing as T

from models.esports.tourney import Tourney, TMSlot

from ..base import EsportsBaseView
from core import Context
import discord

from utils import inputs


class GroupPages(EsportsBaseView):
    def __init__(self, ctx: Context, tourney: Tourney, *, category=None):
        super().__init__(ctx)

        self.last_role: discord.Role = None
        self.tourney = tourney

        self.records: T.List[T.List["TMSlot"]] = None
        self.record: T.List[TMSlot] = None

        self.category: discord.CategoryChannel = category

    async def rendor(self, msg: discord.Message):
        self.records = await self.tourney._get_groups()
        self.record = self.records[0]

        self.message = await msg.edit(embed=self.initial_embed, view=self)

    async def refresh_view(self):
        _e = self.initial_embed
        try:
            self.message = await self.message.edit(embed=_e, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    # async def __get_current_page(self):
    #     self.records

    @property
    def send_channel(self):
        if self.category:
            return ...

    @property
    def ping_role(self):
        if self.last_role:
            return ...

    @property
    def initial_embed(self):
        current_page = self.records.index(self.record) + 1
        _e = discord.Embed(color=0x00FFB3, title=f"{self.tourney.name} - Group {current_page}")
        _e.set_thumbnail(url=getattr(self.ctx.guild.icon, "url", discord.Embed.Empty))

        _e.description = (
            "```\n"
            + "".join(
                [
                    f"Slot {idx:02}  ->  {slot.team_name}\n"
                    for idx, slot in enumerate(self.record, self.tourney.slotlist_start)
                ]
            )
            + "```"
        )

        _e.add_field(name="Send to", value=getattr(self.send_channel, "mention", "`Not-Set`"))
        _e.add_field(name="Ping Role", value=getattr(self.ping_role, "mention", "`Not-Set`"))
        _e.set_footer(text="Page {}/{}".format(current_page, len(self.records)))
        return _e

    @discord.ui.button(emoji="<:left:878668491660623872>")
    async def prev_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        index = self.records.index(self.record)
        if index == 0:
            self.record = self.records[-1]
        else:
            self.record = self.records[index - 1]

        await self.refresh_view()

    @discord.ui.button(label="Skip to...")
    async def skip_to(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        m = await self.ctx.simple("What page do you want to go to? (Enter page number)")
        p = await inputs.integer_input(self.ctx, delete_after=True, timeout=30)
        await self.ctx.safe_delete(m)

        if p > len(self.records) + 1 or p <= 0:
            return await self.ctx.error("Invalid page number.", 4)

        if self.record == self.records[p - 1]:
            return await self.ctx.error("We are already on that page, ya dumb dumb.", 4)

        self.record = self.records[p - 1]
        await self.refresh_view()

    @discord.ui.button(emoji="<:right:878668370331983913>")
    async def next_button(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        index = self.records.index(self.record)
        if index == len(self.records) - 1:
            self.record = self.records[0]
        else:
            self.record = self.records[index + 1]

        await self.refresh_view()

    @discord.ui.button(label="Send to")
    async def send_channl(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(label="Send", style=discord.ButtonStyle.green)
    async def send_now(self, button: discord.Button, interaction: discord.Interaction):
        ...
