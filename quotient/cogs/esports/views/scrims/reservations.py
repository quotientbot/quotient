from datetime import timedelta

import discord
from discord.ext import commands
from lib import (
    EXIT,
    INFO,
    TEXT_CHANNEL,
    convert_to_seconds,
    send_error_embed,
    text_input,
    truncate_string,
)
from models import Scrim, ScrimReservedSlot

from . import ScrimsBtn, ScrimsView
from .utility.buttons import DiscardChanges
from .utility.common import get_scrim_position
from .utility.paginator import NextScrim, PreviousScrim, SkipToScrim


class ScrimReservationsManager(ScrimsView):
    def __init__(self, ctx: commands.Context, scrim: Scrim):
        super().__init__(ctx, timeout=100)

        self.record = scrim

    async def initial_msg(self) -> discord.Embed:

        reserved_slots = await self.record.reserved_slots.all().order_by("num")
        scrims = await Scrim.filter(guild_id=self.ctx.guild.id).order_by("reg_start_time")

        self.clear_items()

        self.add_item(ReserveNewSlot(self.ctx))
        self.add_item(CancelSlotReservation(self.ctx, disabled=not reserved_slots))
        self.add_item(ReservedSlotInfo(self.ctx, disabled=not reserved_slots))

        if len(scrims) > 1:
            self.add_item(PreviousScrim(self.ctx, row=2))
            self.add_item(SkipToScrim(self.ctx, row=2))
            self.add_item(NextScrim(self.ctx, row=2))

        self.add_item(DiscardChanges(self.ctx, label="Back to Main Menu", emoji=EXIT, row=2))

        embed = discord.Embed(color=self.bot.color)
        embed.description = f"**{self.record}  -  Reserved Slots**\n\n"

        if not reserved_slots:
            embed.description += """```No Slots Reserved yet.```"""

        for slot in reserved_slots:
            embed.description += (
                f"`Slot {slot.num:02}` - **{slot.team_name}** [{getattr(slot.leader, 'mention', '`No Leader`')}]: "
                f"{discord.utils.format_dt(slot.reserved_till,'R') if slot.reserved_till else '`Lifetime`'}\n"
            )

        available_to_reserve = [
            i
            for i in range(self.record.slotlist_start_from, self.record.total_slots + self.record.slotlist_start_from)
            if i not in [s.num for s in reserved_slots]
        ]

        if available_to_reserve:
            embed.description += f"\n\n**Available to Reserve**: `Slot {', '.join(map(str, available_to_reserve))}`"

        embed.set_footer(
            text=f"Page - {' / '.join(await get_scrim_position(self.record.pk, self.record.guild_id))}",
            icon_url=self.ctx.author.display_avatar.url,
        )

        return embed

    async def refresh_view(self):
        try:
            self.message = await self.message.edit(embed=await self.initial_msg(), view=self)
        except discord.HTTPException:
            await self.on_timeout()


class ReserveNewSlot(ScrimsBtn):
    view: ScrimReservationsManager

    def __init__(self, ctx: commands.Context):
        super().__init__(ctx, style=discord.ButtonStyle.green, label="Reserve Slot(s)")

    async def callback(self, inter: discord.Interaction):
        await inter.response.defer()

        m = await inter.followup.send(
            embed=self.view.bot.simple_embed(
                "Enter the slot details you want to reserve in the following format:\n"
                "> `Slot Number`,`Team Name`, `Team Owner / Leader`, `Time to Reserve`\n\n"
                "Enter `none` in place of:\n"
                "- `Team Owner` if you want the slot be a management slot.\n"
                "- `Time to Reserve` if you want the reserve time to never expire.\n\n"
                "\n*Don't forget to separate everything with comma (`,`)*\n",
            ).set_image(url="https://cdn.discordapp.com/attachments/851846932593770496/1252935102493884426/reserve_slots_example.gif"),
            ephemeral=True,
        )

        reserved_slots_input = await text_input(self.ctx, delete_after=True)
        await m.delete(delay=0)

        if reserved_slots_input.strip().lower() == "cancel":
            return await inter.followup.send(embed=self.view.bot.error_embed("Alright, Aborting"), delete_after=5, ephemeral=True)

        slots_list = reserved_slots_input.split("\n")
        for slot in slots_list:
            slot_details = slot.split(",")

            try:
                num, team_name, team_owner, time_to_reserve = slot_details
                num = int(num.strip())

                team_name = truncate_string(team_name.strip(), 25)

            except ValueError:
                return await send_error_embed(
                    inter.channel, "The details you entered were not according to the proper format. Please refer to example image.", 6
                )

            owner_id = None
            if team_owner.strip().lower() != "none":
                owner = await commands.MemberConverter().convert(self.ctx, team_owner.strip())
                owner_id = owner.id

            expires = None
            if time_to_reserve.strip().lower() != "none":
                time_in_seconds = convert_to_seconds(time_to_reserve.strip())
                if time_in_seconds:
                    expires = self.view.bot.current_time + timedelta(seconds=time_in_seconds)

            if num not in (
                r := range(self.view.record.slotlist_start_from, self.view.record.total_slots + self.view.record.slotlist_start_from)
            ):
                await send_error_embed(
                    inter.channel,
                    f"The slot-number you entered (`{num}`) cannot be reserved.\n"
                    f"\nThe slot-number must be a number between `{r.start}` and `{r.stop}`",
                    6,
                )

                continue

            await ScrimReservedSlot.filter(scrim=self.view.record, num=num).delete()

            await ScrimReservedSlot.create(
                num=num,
                leader_id=owner_id,
                team_name=team_name,
                scrim=self.view.record,
                reserved_by=inter.user.id,
                reserved_till=expires,
            )

            if expires:
                await self.view.bot.reminders.create_timer(
                    expires,
                    "scrim_slot_reserve",
                    scrim_id=self.view.record.id,
                    leader_id=owner_id,
                    team_name=team_name,
                    num=num,
                )

        await self.view.refresh_view()


class CancelSlotReservation(ScrimsBtn):
    view: ScrimReservationsManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, style=discord.ButtonStyle.red, label="Remove Reserved", disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        reserved_slots = await self.view.record.reserved_slots.all().order_by("num")
        v = ScrimsView(self.ctx, timeout=100.0)
        v.add_item(ReservedSlotSelector(reserved_slots, max_values=len(reserved_slots)))

        m = await self.ctx.send(embed=self.view.bot.simple_embed("Please select the slots you want to remove from reserved: "), view=v)
        await v.wait()

        if v.selected_slots:
            await ScrimReservedSlot.filter(id__in=v.selected_slots).delete()
            await self.view.refresh_view()

        await m.delete(delay=0)


class ReservedSlotInfo(ScrimsBtn):
    view: ScrimReservationsManager

    def __init__(self, ctx: commands.Context, disabled: bool = True):
        super().__init__(ctx, style=discord.ButtonStyle.grey, label="Slot Info", emoji=INFO, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        v = ScrimsView(self.ctx, timeout=100.0)
        v.add_item(
            ReservedSlotSelector(
                await self.view.record.reserved_slots.all().order_by("num"),
                max_values=1,
                placeholder="Select the slot you want to view info about ...",
            )
        )

        m = await interaction.followup.send(
            embed=self.view.bot.simple_embed("Please select the slot you want to view info about: "), view=v
        )
        await v.wait()

        await m.delete(delay=0)

        if v.selected_slots:
            slot = await ScrimReservedSlot.get(id=v.selected_slots[0])

            embed = discord.Embed(color=self.view.bot.color, title=f"**Slot {slot.num}  -  Reserved Info**")
            embed.add_field(name="Team Name", value=slot.team_name, inline=False)
            embed.add_field(name="Reserved By", value=f"<@{slot.reserved_by}>", inline=False)
            embed.add_field(
                name="Reserved For",
                value=f"<@{slot.leader_id}>" if slot.leader_id else "`User not provided`",
                inline=False,
            )

            embed.add_field(name="Reserved At", value=discord.utils.format_dt(slot.reserved_at, "f"), inline=False)
            embed.add_field(
                name="Reserved Till",
                value=discord.utils.format_dt(slot.reserved_till, "f") if slot.reserved_till else "`Lifetime`",
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)


class ReservedSlotSelector(discord.ui.Select):
    view: ScrimsView

    def __init__(
        self,
        reserved_slots: list[ScrimReservedSlot],
        max_values: int,
        placeholder: str = "Select the slot(s) you want to remove from reserved ...",
    ):

        options = []
        for reserved_slot in reserved_slots:
            options.append(
                discord.SelectOption(
                    label=f"Slot {reserved_slot.num}",
                    description=f"Team: {reserved_slot.team_name} ({reserved_slot.leader or 'No leader'})",
                    value=reserved_slot.id.__str__(),
                    emoji=TEXT_CHANNEL,
                )
            )
        super().__init__(
            max_values=max_values,
            placeholder=placeholder,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_slots = self.values
        self.view.stop()
