from __future__ import annotations
from contextlib import suppress

import typing as T
import asyncio
import random
import discord
from discord import ButtonStyle, Interaction, ui

from core import Context
from models import Scrim
from utils import discord_timestamp, emote

from ._ban import ScrimBanManager
from ._base import ScrimsView
from ._design import ScrimDesign
from ._edit import ScrimsEditor
from ._reserve import ScrimsSlotReserve
from ._slotlist import ManageSlotlist
from ._toggle import ScrimsToggle
from ._wiz import ScrimSetup


class ScrimsMain(ScrimsView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100)

        self.ctx = ctx

    async def initial_embed(self):
        _e = discord.Embed(color=0x00FFB3, title="Quotient's Smart Scrims Manager", url=self.ctx.config.SERVER_LINK)

        to_show = []
        for idx, _r in enumerate(await Scrim.filter(guild_id=self.ctx.guild.id).order_by("open_time"), start=1):
            to_show.append(
                f"`{idx}.` {(emote.xmark,emote.check)[_r.stoggle]}: {str(_r)} - {discord_timestamp(_r.open_time,'t')}"
            )

        _e.description = "\n".join(to_show) if to_show else "```Click Create button for new Scrim.```"

        _e.set_footer(
            text="Quotient Prime allows unlimited scrims.",
            icon_url=getattr(self.ctx.author.display_avatar, "url", discord.Embed.Empty),
        )

        if not to_show:
            for _ in self.children[1:]:
                _.disabled = True

        return _e

    @discord.ui.button(label="Create Scrim", style=ButtonStyle.green)
    async def create_new_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        if not await self.ctx.is_premium_guild():
            if await Scrim.filter(guild_id=self.ctx.guild.id).count() >= 3:
                return await self.ctx.premium_mango("Only 3 scrims can be created with free plan.")

        self.stop()
        v = ScrimSetup(self.ctx)
        v.message = await self.message.edit(embed=v.initial_message(), view=v)

    @discord.ui.button(label="Edit Settings", style=ButtonStyle.blurple)
    async def edit_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()
        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        if not scrim:
            return

        v = ScrimsEditor(self.ctx, scrim)
        await v._add_buttons()
        v.message = await self.message.edit(embed=await v.initial_message, view=v)

    @discord.ui.button(label="Instant Start/Stop Reg", style=ButtonStyle.green)
    async def toggle_reg(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(
            self.ctx, multi=False, placeholder="Please select the scrim to stop or start registration."
        )
        self.stop()
        if not scrim:
            return

        v = ScrimsToggle(self.ctx, scrim)
        await v._add_buttons()
        v.message = await self.message.edit(embed=await v.initial_message, view=v)

    @discord.ui.button(label="Reserve Slots", style=ButtonStyle.green)
    async def reserve_slots(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()
        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        if not scrim:
            return

        view = ScrimsSlotReserve(self.ctx, scrim)
        await view.add_buttons()
        view.message = await self.message.edit(embed=await view.initial_embed, view=view)

    @discord.ui.button(label="Ban/Unban", style=ButtonStyle.red)
    async def ban_unban(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()
        if not scrim:
            return

        v = ScrimBanManager(self.ctx, scrim)
        await v._add_buttons()
        v.message = await self.message.edit(embed=await v.initial_message, view=v)

    @discord.ui.button(label="Design", style=ButtonStyle.red)
    async def change_design(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(self.ctx, multi=False)
        self.stop()

        if not scrim:
            return

        view = ScrimDesign(self.ctx, scrim)
        await view._add_buttons()
        view.message = await self.message.edit(embed=await view.initial_embed, view=view)

    @discord.ui.button(label="Manage Slotlist", style=ButtonStyle.blurple)
    async def manage_slotlist(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(
            self.ctx, multi=False, placeholder="Please select the scrim to manage slotlist."
        )

        self.stop()

        if not scrim:
            return

        v = ScrimsView(self.ctx)
        v.add_item(ManageSlotlist(self.ctx, scrim))
        v.message = await self.message.edit("Please choose an action:", embed=None, view=v)

    @discord.ui.button(label="Enable/Disable", style=discord.ButtonStyle.red)
    async def toggle(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()
        scrims = await Scrim.show_selector(self.ctx, multi=True)
        if not scrims:
            return

        self.stop()
        for scrim in scrims:
            await scrim.make_changes(stoggle=not scrim.stoggle)

        await self.ctx.success(
            f"Done! Not that registration of disabled scrims will not be opened, until they are enabled back.", 6
        )

        v = ScrimsMain(self.ctx)
        v.message = await self.message.edit(embed=await v.initial_embed(), view=v)

    @discord.ui.button(label="Scrim not working, Need Help!", style=ButtonStyle.red)
    async def troubleshoot_scrim(self, button: ui.Button, interaction: Interaction):
        await interaction.response.defer()

        scrim = await Scrim.show_selector(
            self.ctx, multi=False, placeholder="Please select the scrim you need help with."
        )

        if not scrim:
            return

        _e = discord.Embed(
            color=self.bot.color, title="Join Support Server for more assistance", url=self.ctx.config.SERVER_LINK
        )
        _e.description = "**Analyzing {0}...**".format(scrim)

        m = await self.ctx.send(embed=_e)
        _results, t, x = [], emote.check, emote.xmark

        _results.append(
            (f"{x} Registration channel not found.", f"{t} Registration channel found.")[bool(scrim.registration_channel)]
        )
        _results.append(
            (f"{x} Slotlist channel not found.", f"{t} Slotlist channel found.")[bool(scrim.slotlist_channel)]
        )

        perms = False
        with suppress(AttributeError):
            perms = scrim.registration_channel.permissions_for(self.ctx.guild.me)
            perms = all(
                (
                    perms.manage_channels,
                    perms.manage_permissions,
                    perms.manage_messages,
                    perms.use_external_emojis,
                    perms.add_reactions,
                    perms.embed_links,
                )
            )
        _results.append(
            (f"{x} Need permissions in registration channel", f"{t} Registration channel permissions are ok.")[perms]
        )

        _results.append((f"{x} Success Role not found.", f"{t} Success Role found.")[bool(scrim.role)])
        _results.append(
            (f"{x} `Manage-Roles` perms required.", f"{t} `Manage-Roles` perms found.")[
                scrim.guild.me.guild_permissions.manage_roles
            ]
        )

        role_perm = False
        if scrim.role:
            if not scrim.role >= scrim.guild.me.top_role:
                role_perm = True

        _results.append((f"{x} Success Role is above my toprole.", f"{t} Success Role is below my toprole.")[role_perm])
        _results.append((f"{x} Open role not found.", f"{t} Open role found.")[bool(scrim.open_role)])
        _results.append((f"{x} Logs-Channel not found", f"{t} Logs-Channel found.")[bool(scrim.logschan)])
        _results.append(f"\nRegistration open time is {discord_timestamp(scrim.open_time,'f')}")
        _results.append(f"{t} Scrim analyzing complete.")

        for _ in _results:
            _e.description += "\n" + _
            await asyncio.sleep(random.randint(1, 3))
            with suppress(discord.HTTPException):
                await m.edit(embed=_e, delete_after=10)
