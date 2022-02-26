from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Context
from ..base import EsportsBaseView

from ._wiz import TourneySetupWizard
import discord

from ._editor import TourneyEditor
from models import Tourney

from discord import ButtonStyle
import asyncio

from utils import emote
from contextlib import suppress


class TourneyManager(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=100, name="Tourney Manager")
        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    async def initial_embed(self) -> discord.Embed:
        to_show = [
            f"`{idx}.` {str(_r)}"
            for idx, _r in enumerate(await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id"), start=1)
        ]

        _e = discord.Embed(color=self.bot.color, title="Smart Tournament Manager", url=self.bot.config.SERVER_LINK)
        _e.description = "\n".join(to_show) if to_show else "```Click Create button for new tourney.```"
        _e.set_thumbnail(url=self.ctx.guild.me.avatar.url)
        _e.set_footer(
            text="Quotient Prime allows unlimited tournaments.",
            icon_url=getattr(self.ctx.author.avatar, "url", discord.Embed.Empty),
        )

        if not to_show:
            for _ in self.children[1:]:
                _.disabled = True

        return _e

    @discord.ui.button(style=ButtonStyle.blurple, custom_id="create_tourney", label="Create Tournament")
    async def create_tournament(self, button: discord.Button, interaction: discord.Interaction):
        self.stop()
        _v = TourneySetupWizard(self.ctx)
        _v.message = await self.message.edit(embed=_v.initial_message(), view=_v)

    @discord.ui.button(style=ButtonStyle.blurple, custom_id="edit_tourney", label="Edit Settings")
    async def edit_tournament(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        records = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id")

        _v = TourneyEditor(self.ctx, records)
        await _v._add_buttons(self.ctx)

        _v.message = await self.message.edit(embed=await _v.initial_message(), view=_v)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="tourney_start_pause", label="Start/Pause Reg")
    async def start_or_pause(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        tourney = await Tourney.prompt_selector(self.ctx, placeholder="Select a tournament to start/pause")
        if tourney:
            p = await self.ctx.prompt(
                f"Are you sure you want to {'pause' if tourney.started_at else 'start'} the registrations of {tourney}?"
            )
            if not p:
                return await self.ctx.error("Ok, Aborting", 4)

            b, r = await tourney.toggle_registrations()
            if not b:
                return await self.ctx.error(r, 4)

            return await self.ctx.success(f"Done! Check {tourney.registration_channel.mention}", 4)

    @discord.ui.button(style=ButtonStyle.blurple, custom_id="ban_unban_tourney", label="Ban/Unban")
    async def ban_or_unban(self, btn: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        tourney = await Tourney.prompt_selector(self.ctx, placeholder="Select a tournament to ban/unban users.")
        if tourney:
            m = await self.ctx.simple("Mention the users you want to ban or unban.")

            msg = None
            with suppress(asyncio.TimeoutError):
                msg: discord.Message = await self.ctx.bot.wait_for(
                    "message", check=lambda m: m.author == self.ctx.author and m.channel == self.ctx.channel, timeout=60
                )

            await m.delete()

            if not msg or not msg.mentions:
                return await self.ctx.error("You need to mention at least one user.", 4)

            await msg.delete()
            banned, unbanned = [], []
            for m in msg.mentions:
                if m.id in tourney.banned_users:
                    await tourney.unban_user(m)
                    unbanned.append(m.mention)

                else:
                    await tourney.ban_user(m)
                    banned.append(m.mention)

        await self.ctx.simple(
            f"{emote.check} | Banned: {', '.join(banned) if banned else 'None'}\n"
            f"{emote.check} | Unbanned: {', '.join(unbanned) if unbanned else 'None'}",
            10,
        )

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="tourney_groups_send", label="Send Groups")
    async def send_tourney_group(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="tourney_rm_slots", label="Cancel Slots")
    async def remove_user_slots(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="tourney_reserv_slots", label="Manually Add Slot")
    async def reserve_user_slot(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="tourney_ch_slotm", label="Slot-Manager channel")
    async def tourney_slotmanager(self, button: discord.Button, interaction: discord.Interaction):
        ...

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="download_excel_data", label="MS Excel File")
    async def download_excel_data(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if not await self.ctx.is_premium_guild():
            return await self.ctx.error(
                "You need Quotient Premium to download Ms Excel file containing all the "
                f"registration data of your tourneys. (Use `{self.ctx.prefix}perks` command)",
                5,
            )

        tourney = await Tourney.prompt_selector(self.ctx, placeholder="Select a tournament to download data...")
        if tourney:
            _m = await self.ctx.simple(f"Crunching the data for you.... {emote.loading}")
            await asyncio.sleep(1)

            _log_chan = await self.bot.getch(self.bot.get_channel, self.bot.fetch_channel, 899185364500099083)
            m = await _log_chan.send(file=await tourney.get_csv())

            e = discord.Embed(
                color=self.bot.color,
                description=(
                    f"**[Click Here]({m.attachments[0].url})** to download `.csv` file "
                    f"containing all the registration records of {tourney}\n\n"
                    "*`To Open`: Use Microsoft Excel, Libre Office or any other softwares that is compatible with .csv files.*"
                ),
            )

            with suppress(discord.HTTPException):
                await _m.edit(embed=e, delete_after=15)

    @discord.ui.button(style=ButtonStyle.blurple, custom_id="fix_tourny", label="Tourney not working :c Fix it Please!")
    async def fix_my_tourney(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
