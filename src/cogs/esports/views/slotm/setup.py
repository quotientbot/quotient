from __future__ import annotations
from code import interact

from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
    from core import Quotient

from ...views.base import EsportsBaseView
from core import Context, QuotientView

from models.esports.slotm import ScrimsSlotManager
from cogs.esports.views.scrims import ScrimSelectorView
import discord

from models import Scrim
from utils import emote, Prompt, truncate_string

from .time import MatchTimeEditor

from .editor import ScrimsSlotmEditor


__all__ = ("ScrimsSlotManagerSetup",)


class ScrimsSlotmSelector(discord.ui.Select):
    def __init__(self, records: List[ScrimsSlotManager]):

        _o = []
        for record in records:
            _o.append(
                discord.SelectOption(
                    label=getattr(record.main_channel, "name", "channel-not-found"),  # type: ignore
                    value=record.id,
                    description=truncate_string(f"Scrims: {', '.join(str(_) for _ in record.scrim_ids)}", 100),
                    emoji=emote.TextChannel,
                )
            )

        super().__init__(placeholder="Select a slot-manager channel ...", options=_o)

    async def callback(self, interaction: discord.Interaction):
        self.view.custom_id = self.values[0]

        self.view.stop()


class ScrimsSlotManagerSetup(EsportsBaseView):
    def __init__(self, ctx: Context):
        super().__init__(ctx, timeout=60, title="Scrims Slot Manager")

        self.ctx = ctx
        self.bot: Quotient = ctx.bot

    @staticmethod
    async def initial_message(guild: discord.Guild):
        records = await ScrimsSlotManager.filter(guild_id=guild.id)
        _to_show = [f"`{idx}.` {_.__str__()}" for idx, _ in enumerate(records, start=1)]

        _sm = "\n".join(_to_show) if _to_show else "```No scrims slot managers found.```"

        _e = discord.Embed(color=0x00FFB3, title=f"Scrims Slot-Manager Setup")

        _e.description = (
            "Slot-Manager is a way to ease-up scrims slot management process. With Quotient's slotm users can - "
            "cancel their slot, claim an empty slot and also set reminder for vacant slots, All without bugging any mod.\n\n"
            f"**Current slot-manager channels:**\n{_sm}\n\nDon't forget to set the match times :)"
        )
        # _e.set_thumbnail(url=guild.me.avatar.url)
        return _e

    @discord.ui.button(label="Add Channel", custom_id="scrims_slotm_addc", emoji=emote.TextChannel)
    async def add_channel(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        available_scrims = await ScrimsSlotManager.available_scrims(self.ctx.guild)
        if not available_scrims:
            return await self.error_embed(
                f"There are no scrims available for a new slotmanager channel.\n\n"
                "If you have other slot-m channel, first remove the scrims from that channel to add them to new slot-m."
            )

        _view = ScrimSelectorView(
            interaction.user, available_scrims, placeholder="Select scrims to add to slot-manager ..."
        )
        await interaction.followup.send(
            "Choose 1 or multiple scrims that you want to add to new slot-manager."
            "\n\n`If a scrim isn't in the dropdown that means it has been addded to another slotm.`",
            view=_view,
            ephemeral=True,
        )
        await _view.wait()

        prompt = Prompt(interaction.user.id)
        await interaction.followup.send(
            "A new channel will be created for the selected scrims slot manager.\n\n`Do you want to continue?`",
            view=prompt,
            ephemeral=True,
        )
        await prompt.wait()

        if not prompt.value:
            return await interaction.followup.send("Alright, Aborting.", ephemeral=True)

        slotm = ScrimsSlotManager(scrim_ids=_view.custom_id, guild_id=interaction.guild_id)
        self.record = await slotm.setup(self.ctx.guild, interaction.user)
        await self.ctx.success(
            f"Successfully setup slotm for selected scrims in {self.record.main_channel.mention}.\n\n"
            "`You can rename this channel if you want to.`",
            10,
        )

    @discord.ui.button(label="Edit Config", custom_id="scrims_slotm_editc", emoji=emote.edit)
    async def edit_config(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        records = await ScrimsSlotManager.filter(guild_id=self.ctx.guild.id)
        if not records:
            return await self.ctx.error(
                "You haven't added any slot-manager channel yet.\n\nClick `Add Channel` to add a new slot-m channel.", 2
            )

        _view = QuotientView(self.ctx)
        _view.add_item(ScrimsSlotmSelector(records))
        # _view.add_item(QuotientView.tricky_invite_button())
        await interaction.followup.send("Kindly choose a slot-manager channel to edit.", view=_view, ephemeral=True)
        await _view.wait()

        if _view.custom_id:
            __record = await ScrimsSlotManager.get(pk=_view.custom_id)

            __editor_view = ScrimsSlotmEditor(self.ctx, record=__record)

            __editor_view.message = await interaction.followup.send(
                embed=__editor_view.initial_embed(), view=__editor_view
            )

    @discord.ui.button(emoji="🔒", label="Match Time", custom_id="scrims_slotm_matcht")
    async def set_match_time(self, button: discord.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        scrims = await Scrim.filter(guild_id=self.ctx.guild.id)
        _to_show = [
            f"{idx}) {getattr(_.registration_channel,'name','deleted-channel').ljust(18)}"
            f"   {_.match_time.strftime('%I:%M %p') if _.match_time else 'Not-Set'}"
            for idx, _ in enumerate(scrims, start=1)
        ]
        _to_show.insert(0, f"   {'Scrims'.ljust(18)}   Match Time\n")

        _e = discord.Embed(color=self.ctx.bot.color, title="Scrims-Match time", url=self.bot.config.SERVER_LINK)

        _to_show = "\n".join(_to_show)
        _e.description = (
            f"Match time means the time when `ID/Pass` \nof that particular scrim is shared.\n```{_to_show}```"
        )

        _e.set_footer(text="Users cannot cancel/claim slots after this time.", icon_url=self.ctx.guild.me.avatar.url)

        _view = QuotientView(self.ctx)
        _view.add_item(MatchTimeEditor(self.ctx))
        _view.add_item(QuotientView.tricky_invite_button())

        _view.message = await interaction.followup.send(embed=_e, view=_view, ephemeral=True)
