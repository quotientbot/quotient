from __future__ import annotations

import typing as T

from models.esports.tourney import Tourney, TMSlot

from ..base import EsportsBaseView
from core import Context
import discord


class GroupPages(EsportsBaseView):
    def __init__(self, ctx: Context, tourney: Tourney, *, category=None):
        super().__init__(ctx)

        self.last_role: discord.Role = None
        self.tourney = tourney
        self.current_page = 1

        self.records: T.List[T.List["TMSlot"]] = None
        self.record: T.List[TMSlot] = None

        self.category: discord.CategoryChannel = category

    async def render(self):
        ...

    # async def refresh_view(self):
    #     _e = await self.__get_current_page()

    #     try:
    #         self.message = await self.message.edit(embed=_e, view=self)
    #     except discord.HTTPException:
    #         await self.on_timeout()

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
        _e = discord.Embed(color=0x00FFB3, title=f"{self.tourney} - Group {current_page}")
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

    @discord.ui.button()
    async def prev_button(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def skip_to(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def next_button(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def send_channel(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button()
    async def send_to(self, button: discord.Button, interaction: discord.Interaction):
        ...
