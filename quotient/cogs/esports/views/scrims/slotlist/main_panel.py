import asyncio
import random
from datetime import timedelta

import discord
from lib import INFO, convert_to_seconds
from tortoise.query_utils import Prefetch

from quotient.models import Scrim, ScrimAssignedSlot, ScrimsBanLog, ScrimsBannedUser

from ..ban_unban import BanFieldsInput
from ..utility.selectors import prompt_scrims_slot_selector
from .edit_panel import ScrimSlotlistEditPanel


class ScrimsSlotlistMainPanel(discord.ui.View):
    message: discord.Message

    def __init__(self, scrim: Scrim):
        super().__init__(timeout=None)

        self.scrim = scrim
        self.bot = scrim.bot

    async def inter_check(self, inter: discord.Interaction) -> bool:
        if not any(
            (
                inter.user.guild_permissions.manage_guild,
                "scrims-mod" in (_.name.strip().lower() for _ in inter.user.roles),
            )
        ):
            return await inter.response.send_message(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=("You need `manage server` permissions or `@scrims-mod` role to edit this slotlist."),
                ),
                ephemeral=True,
            )

        return True

    async def make_sure_scrim_exists(self, inter: discord.Interaction) -> bool:
        self.scrim = await Scrim.get_or_none(id=self.scrim.id).prefetch_related(
            Prefetch("assigned_slots", queryset=ScrimAssignedSlot.all().order_by("num").prefetch_related("scrim"))
        )

        if not self.scrim:
            for c in self.children:
                c.disabled = True
                c.style = discord.ButtonStyle.grey

            await self.message.edit(view=self)
            await inter.followup.send("This scrim doesn't exist anymore.", ephemeral=True)

            return False

        return True

    @discord.ui.button(label="Edit", emoji="📝", style=discord.ButtonStyle.green, custom_id="scrim_slotlist_edit_b")
    async def edit_slotlist(self, inter: discord.Interaction, button: discord.Button):
        await inter.response.defer(thinking=True, ephemeral=True)

        if not await self.make_sure_scrim_exists(inter):
            return

        view = ScrimSlotlistEditPanel(self.scrim)
        view.message = await inter.followup.send(embed=view.initial_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="Punish", emoji="🛠️", style=discord.ButtonStyle.danger, custom_id="scrim_slotlist_ban_b")
    async def ban_slot(self, inter: discord.Interaction, button: discord.Button):
        modal = BanFieldsInput()
        await inter.response.send_modal(modal)

        await modal.wait()

        banned_until = convert_to_seconds(modal.ban_until.value) if modal.ban_until.value else None
        if banned_until:
            banned_until = self.bot.current_time + timedelta(seconds=banned_until)

        if not await self.make_sure_scrim_exists(inter):
            return

        assigned_slots = list(self.scrim.assigned_slots)

        if not assigned_slots:
            return await inter.followup.send("No slot in the scrim to ban.", ephemeral=True)

        slot_to_ban = await prompt_scrims_slot_selector(inter, assigned_slots, "Select the slot to ban team.", multiple=False)
        if not slot_to_ban:
            return

        view = discord.ui.View(timeout=60)
        view.add_item(BanOptions())

        m = await inter.followup.send("", view=view, ephemeral=True)
        await view.wait()

        if not view.value:
            return

        scrim_banlog = await ScrimsBanLog.get_or_none(guild_id=inter.guild_id)

        e = discord.Embed(color=self.bot.color, title="Punished Successfully!", description="")

        if view.value == "leader":
            await ScrimsBannedUser.filter(user_id=slot_to_ban[0].leader_id, guild_id=inter.guild_id).delete()

            record = await ScrimsBannedUser.create(
                user_id=slot_to_ban[0].leader_id,
                guild_id=inter.guild_id,
                banned_until=banned_until,
                banned_by=inter.user.id,
                reason=modal.ban_reason.value,
            )
            if scrim_banlog:
                self.bot.loop.create_task(scrim_banlog.log_ban(record))

            e.description += (
                f"{slot_to_ban[0].leader} *[{slot_to_ban[0].leader_id}]*, has been banned from all scrims.\n\n"
                f"**Reason:** `{modal.ban_reason.value or 'No reason provided.'}`\n"
                f"**Until:** {discord.utils.format_dt(banned_until) if banned_until else 'Indefinite'}"
            )

        else:

            for member in slot_to_ban[0].members:
                await ScrimsBannedUser.filter(user_id=member, guild_id=inter.guild_id).delete()

                record = await ScrimsBannedUser.create(
                    user_id=member,
                    guild_id=inter.guild_id,
                    banned_until=banned_until,
                    banned_by=inter.user.id,
                    reason=modal.ban_reason.value,
                )
                if scrim_banlog:
                    self.bot.loop.create_task(scrim_banlog.log_ban(record))

                e.description += f"{slot_to_ban[0].leader} *[{slot_to_ban[0].leader_id}]*, has been banned from all scrims.\n"

            e.description += (
                f"\n\n**Reason:** `{modal.ban_reason.value or 'No reason provided.'}`\n"
                f"**Until:** {discord.utils.format_dt(banned_until) if banned_until else 'Indefinite'}\n"
            )

        await m.edit(embed=e, view=None)

    @discord.ui.button(label="Info", emoji=INFO, style=discord.ButtonStyle.green, custom_id="scrim_slotlist_info_b")
    async def get_slot_info(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.defer(thinking=True, ephemeral=True)

        if not await self.make_sure_scrim_exists(inter):
            return

        assigned_slots = list(self.scrim.assigned_slots)

        if not assigned_slots:
            return await inter.followup.send("No slot in the scrim to get info.", ephemeral=True)

        slot = await prompt_scrims_slot_selector(inter, assigned_slots, "Select the slot to get info...", multiple=False)
        if not slot:
            return

        leader = await self.bot.get_or_fetch_member(inter.guild, slot[0].leader_id)

        e = discord.Embed(
            color=self.bot.color,
            description=(
                f"**Slot Num:** `{slot[0].num}`\n"
                f"**Name:** `{slot[0].team_name}`\n"
                f"**Captain:** `{leader}` (<@{slot[0].leader_id}>)\n"
                f"**Team:** " + ", ".join([f"<@{i}>" for i in slot[0].members])
            ),
        )

        if slot[0].jump_url:
            e.add_field(name="Registration Message", value=f"[Click me to Jump]({slot[0].jump_url})", inline=False)

        e.set_author(name="Slot Info", icon_url=inter.user.display_avatar.url)
        await inter.followup.send(embed=e, ephemeral=True)


class BanOptions(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Ban Team Leader Only", value="leader", emoji="🛠️"),
            discord.SelectOption(label="Ban All team members", value="player", emoji="🛠️"),
        ]

        super().__init__(
            placeholder="Select the type of ban...",
            options=options,
            max_values=1,
        )

    async def callback(self, inter: discord.Interaction):
        await inter.response.edit_message(view=self.view)
        self.view.value = self.values[0]

        self.view.stop()
