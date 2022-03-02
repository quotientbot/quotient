from __future__ import annotations

from typing import TYPE_CHECKING

from models.esports.tourney import TMSlot

if TYPE_CHECKING:
    from core import Quotient

from core import Context, QuotientView
from ..base import EsportsBaseView

from ._wiz import TourneySetupWizard
import discord

from ._editor import TourneyEditor
from models import Tourney

from discord import ButtonStyle
import asyncio

from utils import emote
from contextlib import suppress
from utils import member_input, plural

from ._select import TourneySlotSelec
from tortoise.query_utils import Q


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

    @discord.ui.button(style=ButtonStyle.blurple, label="Create Tournament")
    async def create_tournament(self, button: discord.Button, interaction: discord.Interaction):
        self.stop()
        _v = TourneySetupWizard(self.ctx)
        _v.message = await self.message.edit(embed=_v.initial_message(), view=_v)

    @discord.ui.button(style=ButtonStyle.blurple, label="Edit Settings")
    async def edit_tournament(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        records = await Tourney.filter(guild_id=self.ctx.guild.id).order_by("id")

        _v = TourneyEditor(self.ctx, records)
        await _v._add_buttons(self.ctx)

        _v.message = await self.message.edit(embed=await _v.initial_message(), view=_v)

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Start/Pause Reg")
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

    @discord.ui.button(style=ButtonStyle.blurple, label="Ban/Unban")
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

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Cancel Slots")
    async def remove_user_slots(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        m = await self.ctx.simple("Mention the user whose slot you want to remove.")
        member = await member_input(self.ctx, delete_after=True)
        await m.delete()

        if not member:
            return await self.ctx.error("You need to mention a user.", 4)

        _slots = []
        async for tourney in Tourney.filter(guild_id=self.ctx.guild.id).order_by("id"):
            async for slot in tourney.assigned_slots.filter(
                Q(Q(leader_id=member.id), Q(members__contains=member.id), join_type="OR")
            ).order_by("num"):
                setattr(slot, "tourney", tourney)
                _slots.append(slot)

        if not _slots:
            return await self.ctx.error(f"{member.mention} don't have any slot in any tourney of this server.", 4)

        _v = QuotientView(self.ctx)
        _v.add_item(TourneySlotSelec(_slots))
        _v.message = await interaction.followup.send("select the slots you want to cancel", view=_v,ephemeral=True)

        await _v.wait()

        if _v.custom_id:
            p = await self.ctx.prompt(
                f"{plural(_v.custom_id):slot|slots} of {member.mention} will be permanently removed.",
                title="Are you sure you want to continue?",
            )
            if not p:
                return await self.ctx.success("Ok, Aborting", 4)

            c = 0
            for _ in _v.custom_id:
                slot_id,tourney_id = _.split(":")
                tourney = await Tourney.get_or_none(id=tourney_id)
                slot = await TMSlot.get_or_none(id=slot_id)

                if not tourney or not slot:
                    print(tourney, slot)
                    continue

                await tourney.remove_slot(slot)
                c += 1

            return await self.ctx.success(f"Done! {c} slot(s) of {member.mention} removed.", 4)

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Manually Add Slot")
    async def reserve_user_slot(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Slot-Manager channel")
    async def tourney_slotmanager(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="MS Excel File")
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

    @discord.ui.button(style=ButtonStyle.blurple, label="Tourney not working :c Fix it Please!")
    async def fix_my_tourney(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
