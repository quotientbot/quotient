from contextlib import suppress

from ..views.base import EsportsBaseView
from core import Context
from models import Tourney

from ..helpers import tourney_work_role

from utils import regional_indicator as ri, inputs, truncate_string

from constants import EsportsRole
from string import ascii_uppercase

import discord


class TourneyEditor(EsportsBaseView):
    def __init__(self, ctx: Context, *, tourney: Tourney):
        super().__init__(ctx, timeout=60, title="Tourney Editor")

        self.ctx = ctx
        self.tourney = tourney

    @staticmethod
    def initial_message(tourney: Tourney) -> discord.Embed:

        slotlist_channel = getattr(tourney.confirm_channel, "mention", "`channel-deleted`")
        registration_channel = getattr(tourney.registration_channel, "mention", "`channel-deleted`")
        tourney_role = getattr(tourney.role, "mention", "`role-deleted`")

        open_role = tourney_work_role(tourney, EsportsRole.open)
        ping_role = tourney_work_role(tourney, EsportsRole.ping)

        embed = discord.Embed(color=0x00FFB3, title=f"Tourney Editor (ID: {tourney.id})")

        fields = {
            "Name": f"`{tourney.name}`",
            "Registration Channel": registration_channel,
            "Confirm Channel": slotlist_channel,
            "Success Role": tourney_role,
            "Mentions": f"`{tourney.required_mentions}`",
            "Ping Role": f"`not-set`" if not ping_role else ping_role,
            "Slots": f"`{tourney.total_slots:,}`",
            "Open Role": open_role,
            "Multi Register": ("`No`", "`Yes`")[tourney.multiregister],
            "Team Name Compulsion": ("`No!`", "`Yes!`")[tourney.teamname_compulsion],
            "Duplicate Team Names": ("`Allowed!`", "`Not Allowed`")[tourney.no_duplicate_name],
            "Autodelete Rejected Reg": ("`No!`", "`Yes!`")[tourney.autodelete_rejected],
        }

        for idx, (name, value) in enumerate(fields.items()):
            embed.add_field(
                name=f"{ri(ascii_uppercase[idx])} {name}:",
                value=value,
            )

        return embed

    async def update_tourney(self, **kwargs):
        await Tourney.filter(pk=self.tourney.id).update(**kwargs)
        await self.__refresh_view()

    async def __refresh_view(self):
        embed = self.initial_message(await self.tourney.refresh_from_db())
        try:
            self.message = await self.message.edit(embed=embed, view=self)
        except discord.HTTPException:
            await self.on_timeout()

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_name", emoji=ri("a"))
    async def set_name(self, button: discord.Button, interaction: discord.Interaction):
        msg = await self.ask_embed(
            "What should be the new name of this tourney?\n\n"
            "`Please Keep this under 30 characters.`"
        )

        new_name = await inputs.string_input(self.ctx, self.check,delete_after=True)

        new_name = truncate_string(new_name.strip(),30)

        await self.ctx.safe_delete(msg)

        await self.update_tourney(name=new_name)

        
    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_reg_channel", emoji=ri("b"))
    async def set_reg_channel(self, button: discord.Button, interaction: discord.Interaction):
        msg = await self.ask_embed(
            "Which channel do you want to use as registration channel.\n\n"
            "`Mention the channel or enter its ID.`"
        )

        channel = await inputs.channel_input(self.ctx, self.check, delete_after=True)
        

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_confirm_channel", emoji=ri("c"))
    async def set_confirm_channel(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_role", emoji=ri("d"))
    async def set_role(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_mentions", emoji=ri("e"))
    async def set_mentions(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_ping", emoji=ri("f"))
    async def set_ping_role(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_slots", emoji=ri("g"))
    async def set_slots(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_open_role", emoji=ri("h"))
    async def set_open_role(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_multireg", emoji=ri("i"))
    async def set_multireg(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_name_compulsion", emoji=ri("j"))
    async def set_slots(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_name_duplicacy", emoji=ri("k"))
    async def set_duplicacy(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.secondary, custom_id="tourney_delete_rejected", emoji=ri("l"))
    async def set_autodelete(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.red, custom_id="tourney_stop_view", label="Stop Editing")
    async def stop_view(self, button: discord.Button, interaction: discord.Interaction):
        ...
