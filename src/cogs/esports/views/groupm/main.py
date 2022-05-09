from __future__ import annotations

import typing as T
from contextlib import suppress

if T.TYPE_CHECKING:
    from core import Quotient

import discord

from core import Context
from models import Tourney
from utils import inputs, keycap_digit

from ..base import EsportsBaseView
from ._paginator import GroupPages

__all__ = ("TourneyGroupManager",)


class TourneyGroupManager(EsportsBaseView):
    def __init__(self, ctx: Context, tourney: Tourney, **kwargs):
        super().__init__(ctx, **kwargs)

        self.tourney = tourney
        self.category = None

        self.ping_all = False

        self.start_from = tourney.slotlist_start

    @property
    def initial_embed(self):
        _e = discord.Embed(
            color=self.ctx.bot.color, title="Tourney Group Management", url=self.tourney.bot.config.SERVER_LINK
        )
        _e.description = (
            f"Use `create channels & roles` to setup tourney groups.\n"
            "Use `Group List` to post group/slotlist in channels."
        )
        _e.add_field(name=f"{keycap_digit(1)} Slotlist Start from", value=f"`Slot {self.start_from}`")
        _e.add_field(name=f"{keycap_digit(2)} Ping @everyone", value=("`No`", "`Yes`")[self.ping_all])
        return _e

    async def __refresh_msg(self):
        with suppress(discord.HTTPException):
            self.message = await self.message.edit(embed=self.initial_embed)

    @discord.ui.button(emoji=keycap_digit(1))
    async def change_slotlist_start(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("Enter the slot number to start group/slotlist. (Max `20`)")
        self.start_from = await inputs.integer_input(self.ctx, limits=(1, 20), delete_after=True)
        await self.ctx.safe_delete(m)

        await self.tourney.make_changes(slotlist_start=self.start_from)
        await self.tourney.refresh_from_db()

        await self.__refresh_msg()

    @discord.ui.button(emoji=keycap_digit(2))
    async def toggle_ping_all(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.ping_all = not self.ping_all
        await self.__refresh_msg()

    @discord.ui.button(label="Create Channels & Roles")
    async def create_roles_channels(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if len(self.ctx.guild.channels) >= 490:
            return await self.ctx.error("Too many channels in server. Please delete some first.", 4)

        _e = discord.Embed(color=0x00FFB3)
        _e.description = (
            "**Enter the format for group roles & channels creation.**\n"
            "*`{0}` will be replaced by the number of group or roles*\n\nExamples:"
        )
        _e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/953163516481777684/unknown.png")

        m = await interaction.followup.send(embed=_e)
        _format = await inputs.string_input(self.ctx, timeout=60, delete_after=True)

        await self.ctx.safe_delete(m)
        if len(_format) > 35:
            return await self.ctx.error("Name too long. Max 35 characters.", 4)

        if not "{0}" in _format:
            return await self.ctx.error("No `{0}` found in input.", 4)

        p = await self.ctx.prompt(
            f"Group Roles/channels will look like this: `{_format.replace('{0}','1')}`,`{_format.replace('{0}','2')}`",
            title="Is this correct?",
        )

        if not p:
            return await self.ctx.error("Cancelled.", 4)
        _e.description = (
            "Enter the range of group numbers to create channels & setup roles.\n"
            "For example:\n"
            "`1-5` will create channels for group 1 to 5 and setup roles."
        )
        _e.set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/955013587049525278/unknown.png")
        m = await interaction.followup.send(embed=_e)
        _range = await inputs.string_input(self.ctx, delete_after=True)
        await self.ctx.safe_delete(m)
        _range = _range.strip().split("-")
        if not len(_range) == 2:
            return await self.ctx.error("Invalid format provided.", 4)
        try:
            x, y = tuple(map(int, _range))
        except ValueError:
            return await self.ctx.error("Invalid format provided.", 4)

        if x == y:
            return await self.ctx.error("Invalid range provided.", 4)

        cat_name = _format.replace("{0}", "") + f" {x}-{y}"

        overwrites = {
            self.ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        if mod := self.tourney.modrole:
            overwrites[mod] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                mention_everyone=True,
            )

        await self.ctx.simple(f"Please wait ...", 5)
        category = await self.ctx.guild.create_category(
            name=cat_name, overwrites=overwrites, reason="for group management by {0}".format(self.ctx.author)
        )
        self.category = category
        for i in range(x, y + 1):
            role = await self.__get_or_create_role(_format.replace("{0}", str(i)))
            if not isinstance(role, discord.Role):
                return await self.ctx.error(role, 10)

            _n = {
                role: discord.PermissionOverwrite(read_messages=True, send_messages=False, read_message_history=True),
                **overwrites,
            }
            try:
                await self.category.create_text_channel(_format.replace("{0}", str(i)), overwrites=_n)
            except Exception as e:
                return await self.ctx.error(e)

        await self.ctx.simple("Group channels and roles creation successfuly", 5)

    @discord.ui.button(label="Group List", style=discord.ButtonStyle.green)
    async def send_grouplist(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if not self.tourney.group_size:
            return await self.ctx.error(
                "**Group size/Teams Per Group is not set.**\n\n"
                "Please press `Go Back` and click on Edit Settings to set Group Size.",
                6,
            )

        if not await self.tourney.assigned_slots.all():
            return await self.ctx.error("Noboby registered yet.", 4)

        self.stop()
        _v = GroupPages(self.ctx, self.tourney, ping_all=self.ping_all, category=self.category)
        await _v.rendor(self.message)

    async def __get_or_create_role(self, name: str) -> T.Union[discord.Role, str]:
        role = discord.utils.get(self.ctx.guild.roles, name=name)
        if role:
            return role

        try:
            role = await self.ctx.guild.create_role(
                name=name, reason="created for group management by {0}".format(self.ctx.author)
            )
        except Exception as e:
            return e

        else:
            return role
