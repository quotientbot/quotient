from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from core import Quotient

from contextlib import suppress
from functools import wraps

import discord
from tortoise.exceptions import OperationalError

from cogs.esports.views.scrims import ScrimSelectorView
from models import ArrayAppend, ArrayRemove, AssignedSlot, Scrim, ScrimsSlotReminder
from models.esports.slotm import ScrimsSlotManager
from utils import BaseSelector, Prompt, plural, emote

__all__ = ("ScrimsSlotmPublicView",)


class scrimsslotmdefer:
    def __call__(self, fn):
        @wraps(fn)
        async def wrapper(view: ScrimsSlotmPublicView, button: discord.Button, interaction: discord.Interaction):
            await interaction.response.defer()

            try:
                await view.record.refresh_from_db()
            except OperationalError:
                await interaction.followup.send("This slot-m is unusable.", ephemeral=True)
                return await interaction.delete_original_message()

            return await fn(view, button, interaction)

        return wrapper


class CancelSlotSelector(discord.ui.Select):
    def __init__(self, records: List[Tuple(AssignedSlot, Scrim)]):

        _options = []
        for record in records:
            slot, scrim = record

            slot: AssignedSlot
            scrim: Scrim

            _options.append(
                discord.SelectOption(
                    label=f"Slot {slot.num} ─ #{getattr(scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{slot.team_name} (ID: {scrim.id})",
                    value=f"{scrim.id}:{slot.id}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder="Select slot from this dropdown", options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class UserSelector(discord.ui.Select):
    def __init__(self, users: List[discord.Member]):
        _options = []
        for user in users:
            _options.append(
                discord.SelectOption(
                    label=f"{user.name}#{user.discriminator}",
                    value=user.id,
                    emoji="📇",
                )
            )

        super().__init__(placeholder="Select your teammate from this dropdown", options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class ClaimSlotSelector(discord.ui.Select):
    def __init__(self, scrims: List[Scrim]):

        _options = []
        for scrim in scrims:
            slots = sorted(scrim.available_slots)

            _options.append(
                discord.SelectOption(
                    label=f"Slot {slots[0]} ─ #{getattr(scrim.registration_channel,'name','deleted-channel')}",
                    description=f"{scrim.name} (ID: {scrim.id})",
                    value=f"{scrim.id}:{slots[0]}",
                    emoji="📇",
                )
            )

        super().__init__(placeholder="Select a slot from this dropdown", options=_options)

    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        self.view.custom_id = interaction.data["values"][0]


class ScrimsSlotmPublicView(discord.ui.View):
    def __init__(self, bot: Quotient, *, record: ScrimsSlotManager):
        super().__init__(timeout=None)

        self.record = record
        self.bot = bot

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id="scrims_slot_cancel", label="Cancel Slot")
    @scrimsslotmdefer()
    async def cancel_scrims_slot(self, button: discord.Button, interaction: discord.Interaction):
        scrims = Scrim.filter(
            pk__in=self.record.scrim_ids,
            closed_at__gt=self.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
            match_time__gt=self.bot.current_time,
            opened_at__isnull=True,
        ).order_by("open_time")

        _user_slots = []

        async for scrim in scrims:
            async for slot in scrim.assigned_slots.filter(user_id=interaction.user.id).order_by("num"):
                _user_slots.append((slot, scrim))

        if not _user_slots:
            return await interaction.followup.send("You don't have any slot to cancel.", ephemeral=True)

        _user_slots = _user_slots[:25]
        cancel_view = BaseSelector(interaction.user.id, CancelSlotSelector, records=_user_slots)
        await interaction.followup.send("Choose a slot to cancel", view=cancel_view, ephemeral=True)
        await cancel_view.wait()

        if c_id := cancel_view.custom_id:
            prompt = Prompt(interaction.user.id)
            await interaction.followup.send("Are you sure you want to cancel your slot?", view=prompt, ephemeral=True)
            await prompt.wait()
            if not prompt.value:
                return await interaction.followup.send("Alright, Aborting.", ephemeral=True)

            scrim_id, slot_id = c_id.split(":")
            scrim = await Scrim.get(pk=scrim_id)

            if not await scrim.assigned_slots.filter(user_id=interaction.user.id, pk__not=slot_id).exists():
                with suppress(discord.HTTPException):
                    await interaction.user.remove_roles(scrim.role)

            _slot = await AssignedSlot.filter(pk=slot_id).first()

            await AssignedSlot.filter(pk=slot_id).update(team_name="Cancelled Slot")
            await scrim.refresh_slotlist_message()
            await _slot.delete()

            await Scrim.filter(pk=scrim_id).update(available_slots=ArrayAppend("available_slots", _slot.num))

            await self.record.refresh_public_message()
            await interaction.followup.send("Alright, Cancelled your slot.", ephemeral=True)

            link = f"https://discord.com/channels/{self.record.guild_id}/{self.record.main_channel_id}/{self.record.message_id}"
            await scrim.dispatch_reminders(slot, interaction.channel, link)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="scrims_slot_claim", label="Claim Slot")
    @scrimsslotmdefer()
    async def claim_scrims_slot(self, button: discord.Button, interaction: discord.Interaction):

        perms = interaction.channel.permissions_for(interaction.guild.me)
        if not perms.manage_channels and perms.manage_messages:
            return await interaction.followup.send(
                "I need `manage_channels` & `manage_messages` permissions in this channel to work properly."
            )

        scrims = await Scrim.filter(
            pk__in=self.record.scrim_ids,
            closed_at__gt=self.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
            match_time__gt=self.bot.current_time,
            opened_at__isnull=True,
            available_slots__not=[],
        ).order_by("open_time")

        for scrim in scrims[:]:
            if not self.record.multiple_slots:
                if await scrim.assigned_slots.filter(user_id=interaction.user.id).exists():
                    scrims.remove(scrim)

            if await scrim.banned_teams.filter(user_id=interaction.user.id).exists():
                with suppress(ValueError):
                    scrims.remove(scrim)

        if not scrims:
            return await interaction.followup.send(
                "**No slot available for you due one of the following reasons:**\n"
                "\n- You already have a slot in the scrim."
                "\n- You are banned from of the scrim.",
                ephemeral=True,
            )

        scrims = scrims[:25]
        claim_view = BaseSelector(interaction.user.id, ClaimSlotSelector, scrims=scrims)
        await interaction.followup.send("Choose a scrim to claim slot from the dropdown", view=claim_view, ephemeral=True)
        await claim_view.wait()
        if c_id := claim_view.custom_id:
            scrim_id, num = c_id.split(":")
            num = int(num)

            scrim = await Scrim.get(pk=scrim_id)

            await interaction.followup.send(
                "What is your team's name?\n\n`Kindly enter your team name or full format.`",
                ephemeral=True,
            )

            team_name = await self.record.get_team_name(interaction)
            if not team_name:
                return

            await scrim.refresh_from_db(("available_slots",))

            if num not in scrim.available_slots:
                return await interaction.followup.send("Somebody just claimed the slot before you.", ephemeral=True)

            await Scrim.filter(pk=scrim_id).update(available_slots=ArrayRemove("available_slots", num))

            with suppress(discord.HTTPException):
                if not (role := scrim.role) in interaction.user.roles:
                    await interaction.user.add_roles(role)

            user_id = interaction.user.id
            _slot = await AssignedSlot.create(num=num, user_id=user_id, members=[user_id], team_name=team_name)
            await scrim.assigned_slots.add(_slot)

            await scrim.refresh_slotlist_message()

            await self.record.refresh_public_message()
            with suppress(AttributeError, discord.HTTPException):
                await scrim.slotlist_channel.send(f"{team_name} ({interaction.user.mention}) -> Claimed Slot {num}")

    @discord.ui.button(label="Remind Me", custom_id="scrims_slot_reminder", emoji="🔔")
    @scrimsslotmdefer()
    async def set_slot_reminder(self, button: discord.Button, interaction: discord.Interaction):
        scrims = await Scrim.filter(
            pk__in=self.record.scrim_ids,
            closed_at__gt=self.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
            match_time__gt=self.bot.current_time,
            opened_at__isnull=True,
            available_slots=[],
        ).order_by("open_time")

        for scrim in scrims[:]:  # create a copy of the list then iterate

            if not self.record.multiple_slots:
                if await scrim.assigned_slots.filter(user_id=interaction.user.id).exists():
                    scrims.remove(scrim)

            if await scrim.banned_teams.filter(user_id=interaction.user.id).exists():
                with suppress(ValueError):
                    scrims.remove(scrim)

            elif await scrim.slot_reminders.filter(user_id=interaction.user.id).exists():
                with suppress(ValueError):
                    scrims.remove(scrim)

        if not scrims:
            return await interaction.followup.send(
                "**No scrim available due one of the following reasons:**\n"
                "\n- You already have a slot in the scrim."
                "\n- You are banned from of the scrim."
                "\n- You already have a slot reminder set of that scrim.",
                ephemeral=True,
            )

        scrims = scrims[:25]
        _view = ScrimSelectorView(interaction.user, scrims, placeholder="Select scrims to add slot reminder")

        await interaction.followup.send(
            "Select 1 or multiple scrims to set reminder\n\n*By selecting scrims, you confirm that Quotient can "
            "DM you when any slot is available of the selected scrims.*",
            view=_view,
            ephemeral=True,
        )
        await _view.wait()
        if not _view.custom_id:
            return

        scrims = await Scrim.filter(pk__in=_view.custom_id)

        for _ in scrims:
            _r = await ScrimsSlotReminder.create(user_id=interaction.user.id)
            await _.slot_reminders.add(_r)

        _e = discord.Embed(
            color=0x00FFB3, description=f"Successfully created reminder for {plural(scrims):scrim|scrims}."
        )

        await interaction.followup.send(embed=_e, ephemeral=True)

    @discord.ui.button(label="Transfer IDP Role", custom_id="scrims_transfer_idp_role", style=discord.ButtonStyle.green)
    @scrimsslotmdefer()
    async def transfer_idp(self, button: discord.Button, interaction: discord.Interaction):

        scrims = Scrim.filter(
            pk__in=self.record.scrim_ids,
            closed_at__gt=self.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
            match_time__gt=self.bot.current_time,
            opened_at__isnull=True,
        ).order_by("open_time")

        _user_slots = []

        async for scrim in scrims:
            async for slot in scrim.assigned_slots.filter(user_id=interaction.user.id).order_by("num"):
                _user_slots.append((slot, scrim))

        if not _user_slots:
            return await interaction.followup.send("You don't have any slot that can be transferred.", ephemeral=True)

        _user_slots = _user_slots[:25]
        cancel_view = BaseSelector(interaction.user.id, CancelSlotSelector, records=_user_slots)
        await interaction.followup.send(
            "Choose a slot to transfer ID-Pass Role to your teammates.", view=cancel_view, ephemeral=True
        )
        await cancel_view.wait()

        if c_id := cancel_view.custom_id:
            try:
                scrim_id, slot_id = c_id.split(":")

                scrim = await Scrim.get(pk=scrim_id)

                _slot = await AssignedSlot.filter(pk=slot_id).first()
                _slot.members.remove(interaction.user.id)
                if not _slot.members:
                    return await interaction.followup.send(
                        f"{interaction.user.mention}, you cannot transfer ID-Pass role to your teammates "
                        "because you didn't mention them during registration.",
                        ephemeral=True,
                    )

                users = []
                for _ in _slot.members:
                    if user := await self.bot.get_or_fetch_member(interaction.guild, _):
                        users.append(user)

                if not users:
                    return await interaction.followup.send("All your teammates have left the server.", ephemeral=True)

                if len(users) == 1:
                    user_id = users[0].id

                else:
                    users_view = BaseSelector(interaction.user.id, UserSelector, users=users)
                    await interaction.followup.send(
                        "Please select your teammate to transfer ID-Pass Role.", view=users_view, ephemeral=True
                    )
                    await users_view.wait()
                    user_id = users_view.custom_id

                await AssignedSlot.filter(pk=_slot.pk).update(user_id=user_id)
                self.bot.loop.create_task(interaction.user.remove_roles(discord.Object(scrim.role_id)))
                self.bot.loop.create_task(interaction.guild.get_member(user_id).add_roles(discord.Object(scrim.role_id)))
                return await interaction.followup.send(
                    f"{emote.check} | ID-Pass Role & Slot ownership transferred to <@{user_id}>", ephemeral=True
                )

            except Exception as e:
                await interaction.followup.send(
                    f"{emote.xmark} | Something went wrong. We are already fixing it.", ephemeral=True
                )
                await self.bot.get_user(548163406537162782).send(e)

    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction) -> None:
        print(error)
