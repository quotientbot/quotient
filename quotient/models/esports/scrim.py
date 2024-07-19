import asyncio

import discord
from humanize import precisedelta
from lib import plural
from models import BaseDbModel
from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField

from ..others import Timer
from .enums import DayType, IdpShareType
from .utility import default_reg_close_msg, default_reg_open_msg, default_slotlist_msg


class ScrimsSlotManager(BaseDbModel):
    class Meta:
        table = "scrims_slot_manager"

    id = fields.IntField(pk=True)
    guild_id = fields.BigIntField()

    channel_id = fields.BigIntField()
    message_id = fields.BigIntField()

    allow_multiple_slots = fields.BooleanField(default=False)

    scrims: fields.ReverseRelation["Scrim"]

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    async def get_public_msg(self) -> discord.Message | None:
        return await self.bot.get_or_fetch_message(self.channel_id, self.message_id)

    async def get_public_embed(self) -> tuple[discord.Embed, discord.ui.View]:
        from cogs.esports.views.scrims.slotm.public_panel import ScrimSlotmPublicPanel

        available_scrims = await self.claimable_scrims()
        view = ScrimSlotmPublicPanel(self)

        e = discord.Embed(color=self.bot.color, title="Scrims Slot Manager", url=self.bot.config("SUPPORT_SERVER_LINK"))
        e.description = (
            f"● Press `Cancel Slot` to cancel your slot.\n"
            f"● Press `Remind Me` to get a reminder is desired slot is unavailable.\n\n"
            f"● Available Slots: \n"
        )

        if not available_scrims:
            e.description += "```No Slots Available at the time.\nPress 🔔 to set a reminder. ``` \n"
            view.children[1].disabled = True

        for idx, scrim in enumerate(available_scrims, start=1):
            e.description += f"`{idx}` {getattr(scrim.registration_channel, 'mention','deleted-channel')}  ─  {plural(scrim.available_slots):Slot|Slots}\n"

        return e, view

    async def refresh_public_message(self):
        msg = await self.get_public_msg()
        if not msg:
            return

        e, v = await self.get_public_embed()
        await msg.edit(content="", embed=e, view=v)

    async def get_user_slots(self, user_id: int) -> list["ScrimAssignedSlot"]:
        return await ScrimAssignedSlot.filter(scrim__slotm=self, members__contains=user_id).prefetch_related("scrim").order_by("num")

    async def full_delete(self):
        await Scrim.filter(slotm=self).update(slotm_id=None)
        await self.delete()

        msg = await self.get_public_msg()
        if msg:
            await msg.delete(delay=0)

    async def claimable_scrims(self):
        return (
            await Scrim.filter(
                slotm=self,
                reg_ended_at__gt=self.bot.current_time.replace(hour=0, minute=0, second=0, microsecond=0),
                available_slots__not=[],
                match_start_time__gt=self.bot.current_time,
                reg_started_at__isnull=True,
            )
            .order_by("reg_start_time")
            .limit(25)
        )

    async def dispatch_reminders(self, scrim_id: int):
        reminders = await ScrimSlotReminder.filter(scrim_id=scrim_id)
        scrim = await Scrim.get_or_none(id=scrim_id)

        if not reminders:
            return

        slotm_link = f"https://discord.com/channels/{self.guild_id}/{self.channel_id}/{self.message_id}"
        e = discord.Embed(color=self.bot.color, title=f"Slot Available To Claim - {self.guild}", url=slotm_link)
        e.description = f"A slot of {scrim} is now available to claim! {plural(reminders):User|Users} want to claim it."

        v = discord.ui.View(timeout=None)
        v.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label="Click me to Claim Slot", url=slotm_link))
        async for user in self.bot.resolve_member_ids(self.guild, [reminder.user_id for reminder in reminders]):
            try:
                await user.send(embed=e, view=v)
            except discord.Forbidden:
                pass

        await ScrimSlotReminder.filter(scrim_id=scrim_id).delete()


class ScrimSlotReminder(BaseDbModel):
    class Meta:
        table = "scrims_slot_reminders"

    id = fields.IntField(primary_key=True)
    scrim_id = fields.IntField()
    user_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)


class Scrim(BaseDbModel):

    class Meta:
        table = "scrims"

    id = fields.IntField(primary_key=True, db_index=True)
    slotm: fields.ForeignKeyRelation[ScrimsSlotManager] = fields.ForeignKeyField(
        "default.ScrimsSlotManager", related_name="scrims", null=True
    )

    guild_id = fields.BigIntField(db_index=True)
    registration_channel_id = fields.BigIntField(db_index=True)

    idp_message_id = fields.BigIntField(null=True)
    idp_share_type = fields.IntEnumField(IdpShareType, default=IdpShareType.LEADER_ONLY)

    slotlist_message_id = fields.BigIntField(null=True)
    slotlist_start_from = fields.SmallIntField(default=1)
    autosend_slotlist = fields.BooleanField(default=True)

    required_mentions = fields.SmallIntField(default=4)

    available_slots = ArrayField("SMALLINT", default=list)
    total_slots = fields.SmallIntField()

    reg_start_time = fields.DatetimeField()
    reg_auto_end_time = fields.DatetimeField(null=True)  # time when registration will end automatically if not closed
    match_start_time = fields.DatetimeField(null=True)  # time when actual game will start
    reg_started_at = fields.DatetimeField(null=True)
    reg_ended_at = fields.DatetimeField(null=True)

    autoclean_channel_time = fields.DatetimeField(null=True)

    reg_start_ping_role_id = fields.BigIntField(null=True)
    reg_end_ping_role_id = fields.BigIntField(null=True)
    open_role_id = fields.BigIntField(null=True)

    allow_multiple_registrations = fields.BooleanField(default=True)  # whether same user can register multiple times
    autodelete_rejected_registrations = fields.BooleanField(default=False)
    autodelete_extra_msges = fields.BooleanField(default=False)
    allow_without_teamname = fields.BooleanField(default=False)
    allow_duplicate_teamname = fields.BooleanField(default=True)  # whether same team name can be used multiple times
    allow_duplicate_mentions = fields.BooleanField(default=True)  # whether same user can be mentioned in multiple regs

    registration_time_elapsed = fields.SmallIntField(default=0)  # in seconds

    registration_open_days = ArrayField("SMALLINT", default=lambda: list([day.value for day in DayType]))

    slotlist_msg_design = fields.JSONField(default=default_slotlist_msg().to_dict())
    open_msg_design = fields.JSONField(default=default_reg_open_msg().to_dict())
    close_msg_design = fields.JSONField(default=default_reg_close_msg().to_dict())

    reactions = ArrayField("VARCHAR(50)", default=lambda: list(["✅", "❌"]))
    required_lines = fields.SmallIntField(default=0)
    scrim_status = fields.BooleanField(default=True)

    drop_panel_message_id = fields.BigIntField(null=True)
    game_maps = fields.JSONField(default={d.name: None for d in DayType})

    assigned_slots: fields.ReverseRelation["ScrimAssignedSlot"]
    reserved_slots: fields.ReverseRelation["ScrimReservedSlot"]

    def __str__(self):
        return f"{getattr(self.registration_channel,'mention','deleted-channel')} (ID: {self.id})"

    @staticmethod
    def is_ignorable(member: discord.Member) -> bool:
        """
        If the member has `scrims-mod` role, they can be ignored in registration channels.
        """
        return "scrims-mod" in (role.name.lower() for role in member.roles)

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def registration_channel(self):
        return self.guild.get_channel(self.registration_channel_id)

    @property
    def scrims_mod_role(self):
        return discord.utils.get(self.guild.roles, name="scrims-mod")

    @property
    def logs_channel(self):
        return discord.utils.get(self.guild.text_channels, name="quotient-scrims-logs")

    @property
    def tick_emoji(self):
        try:
            return self.reactions[0]
        except IndexError:
            return "✅"

    @property
    def cross_emoji(self):
        try:
            return self.reactions[1]
        except IndexError:
            return "❌"

    @property
    def start_ping_role(self):
        return self.guild.get_role(self.reg_start_ping_role_id)

    @property
    def end_ping_role(self):
        return self.guild.get_role(self.reg_end_ping_role_id)

    @property
    def open_role(self):
        return (self.guild.get_role(self.open_role_id), self.guild.default_role)[not self.open_role_id]

    @property
    def pretty_registration_days(self):
        day_abbr = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        return ", ".join([day_abbr[day] for day in self.registration_open_days])

    async def add_tick(self, msg: discord.Message):
        try:
            await msg.add_reaction(self.tick_emoji)
        except discord.HTTPException:
            pass

    async def full_delete(self):
        await ScrimAssignedSlot.filter(scrim_id=self.id).delete()
        await ScrimReservedSlot.filter(scrim_id=self.id).delete()
        await ScrimSlotReminder.filter(scrim_id=self.id).delete()
        await self.delete()

    @property
    async def registration_open_embed(self):
        placeholders = {
            "<<mentions>>": self.required_mentions,
            "<<slots>>": self.total_slots,
            "<<reserved>>": len(self.reserved_slots),
            "<<multireg>>": "Allowed" if self.allow_multiple_registrations else "Not Allowed",
            "<<start_time>>": discord.utils.format_dt(self.match_start_time, "R") if self.match_start_time else "Not Set",
        }

        embed = discord.Embed.from_dict(self.open_msg_design)

        for key, value in placeholders.items():
            embed.title = embed.title.replace(key, str(value)) if embed.title else ""
            embed.description = embed.description.replace(key, str(value)) if embed.description else ""
            embed.set_footer(
                text=embed.footer.text.replace(key, str(value)) if embed.footer.text else "", icon_url=embed.footer.icon_url
            )

        return embed

    @property
    async def registration_close_embed(self):
        placeholders = {
            "<<slots>>": self.required_mentions,
            "<<filled>>": len(self.assigned_slots),
            "<<time_taken>>": precisedelta(self.registration_time_elapsed),
            "<<open_time>>": discord.utils.format_dt(self.reg_start_time, "R"),
            "<<start_time>>": discord.utils.format_dt(self.match_start_time, "R") if self.match_start_time else "Not Set",
        }

        embed = discord.Embed.from_dict(self.close_msg_design)

        for key, value in placeholders.items():
            embed.title = embed.title.replace(key, str(value)) if embed.title else ""
            embed.description = embed.description.replace(key, str(value)) if embed.description else ""
            embed.set_footer(
                text=embed.footer.text.replace(key, str(value)) if embed.footer.text else "", icon_url=embed.footer.icon_url
            )
        return embed

    async def refresh_timers(self):
        """
        Delete the timers and create new ones.
        """

        await Timer.filter(
            extra={"args": [], "kwargs": {"scrim_id": self.id}},
            event__in=["scrim_reg_start", "scrim_reg_end", "scrim_channel_autoclean", "scrims_match_start"],
        ).delete()

        await self.bot.reminders.create_timer(self.reg_start_time, "scrim_reg_start", scrim_id=self.id)
        if self.reg_auto_end_time:
            await self.bot.reminders.create_timer(self.reg_auto_end_time, "scrim_reg_end", scrim_id=self.id)
        if self.autoclean_channel_time:
            await self.bot.reminders.create_timer(self.autoclean_channel_time, "scrim_channel_autoclean", scrim_id=self.id)

        await self.bot.reminders.create_timer(self.match_start_time, "scrims_match_start", scrim_id=self.id)

    async def create_slotlist(self) -> tuple[discord.Embed, discord.ui.View]:
        from cogs.esports.views.scrims.slotlist.main_panel import (
            ScrimsSlotlistMainPanel,
        )

        slotlist_msg = ""

        await self.fetch_related("assigned_slots")

        for idx in range(self.slotlist_start_from, self.total_slots + self.slotlist_start_from):
            slot = next((i for i in self.assigned_slots if i.num == idx), None)
            if slot:
                slotlist_msg += f"S{idx:02}  ->  {slot.team_name}\n"
            else:
                slotlist_msg += f"S{idx:02}  ->  __\n"

        placeholders = {
            "<<name>>": self.registration_channel.name,
            "<<time_taken>>": precisedelta(self.registration_time_elapsed),
            "<<open_time>>": discord.utils.format_dt(self.reg_start_time, "R"),
            "<<slots>>": slotlist_msg,
        }
        embed = discord.Embed.from_dict(self.slotlist_msg_design)

        for k, v in placeholders.items():
            embed.title = embed.title.replace(k, str(v)) if embed.title else ""
            embed.description = embed.description.replace(k, str(v)) if embed.description else ""
            embed.set_footer(text=embed.footer.text.replace(k, str(v)) if embed.footer.text else "", icon_url=embed.footer.icon_url)

        view = ScrimsSlotlistMainPanel(self)
        return embed, view

    async def send_slotlist(self) -> discord.Message:
        e, v = await self.create_slotlist()

        try:
            v.message = await self.registration_channel.send(embed=e, view=v)
        except discord.HTTPException:
            return

        self.slotlist_message_id = v.message.id
        await self.save(update_fields=["slotlist_message_id"])
        return v.message

    async def refresh_slotlist_message(self):
        e, v = await self.create_slotlist()

        try:
            await self.registration_channel.get_partial_message(self.slotlist_message_id).edit(embed=e, view=v)
        except discord.HTTPException:
            m = await self.registration_channel.send(embed=e, view=v)
            self.slotlist_message_id = m.id
            await self.save(update_fields=["slotlist_message_id"])

    async def send_drop_panel(self):
        from cogs.esports.views.scrims.drop_panel.after_scrim import (
            DropLocationSelectorView,
        )

        v = DropLocationSelectorView(self)
        e, f = await v.initial_msg()
        try:
            v.message = await self.registration_channel.send(content="", embed=e, view=v, file=f)
            self.bot.logger.debug(f"Drop Panel Message ID: {v.message.id}, Sent in #{self.registration_channel}")
        except discord.HTTPException:
            return
        else:
            self.drop_panel_message_id = v.message.id
            await self.save(update_fields=["drop_panel_message_id"])

    async def start_registration(self):

        await ScrimAssignedSlot.filter(scrim_id=self.id).delete()

        # Put all available slots in the database (after removing reserved ones)
        self.available_slots = sorted(
            [
                slot_num
                for slot_num in range(self.slotlist_start_from, self.total_slots + self.slotlist_start_from)
                if not slot_num in [slot.num for slot in self.reserved_slots]
            ]
        )

        for reserved_slot in self.reserved_slots:
            await ScrimAssignedSlot.create(
                num=reserved_slot.num,
                leader_id=reserved_slot.leader_id,
                team_name=reserved_slot.team_name,
                jump_url=None,
            )

        self.reg_started_at = self.bot.current_time
        self.reg_ended_at = None
        self.slotlist_message_id = None

        await self.save(update_fields=["reg_started_at", "reg_ended_at", "slotlist_message_id", "available_slots"])
        await asyncio.sleep(0.2)

        self.bot.cache.scrim_channel_ids.add(self.registration_channel_id)

        await self.registration_channel.send(
            getattr(self.start_ping_role, "mention", ""),
            embed=await self.registration_open_embed,
            allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
        )

        await self.send_log(
            f"Registration of {self} has been started successfully.",
            title="Scrims Registration Open",
            color=discord.Color.green(),
            add_contact_btn=False,
        )
        from lib import toggle_channel_perms

        await toggle_channel_perms(self.registration_channel, self.open_role, True)

    async def close_registration(self):
        await self.fetch_related("assigned_slots", "slotm")

        self.reg_ended_at = self.bot.current_time
        self.registration_time_elapsed = (self.reg_ended_at - self.reg_started_at).total_seconds()
        self.reg_started_at = None

        await self.save(update_fields=["reg_ended_at", "registration_time_elapsed", "reg_started_at"])

        from lib import toggle_channel_perms

        registration_channel = self.registration_channel
        await toggle_channel_perms(registration_channel, self.open_role, False)

        try:
            await registration_channel.send(
                getattr(self.end_ping_role, "mention", ""),
                embed=await self.registration_close_embed,
                allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
            )
        except discord.HTTPException:
            return

        if self.autosend_slotlist and self.assigned_slots:
            await self.send_slotlist()

        if self.game_maps[self.bot.current_time.strftime("%A").upper()]:
            await self.send_drop_panel()

        if self.autodelete_extra_msges:
            reg_msg_ids = [i.message_id for i in self.assigned_slots]

            check = lambda x: all(
                (not x.pinned, not x.reactions, not x.embeds, not x.author.id == self.bot.user.id, not x.id in reg_msg_ids)
            )
            self.bot.loop.create_task(self.bot.wait_and_purge(registration_channel, limit=50, wait_for=60, check=check))

        if self.slotm:
            await self.slotm.refresh_public_message()

    async def confirm_change_for_all_scrims(self, target: discord.Interaction, **kwargs):
        """
        Confirm if the current change should be applied to other scrims
        """

        scrims = await Scrim.filter(guild_id=self.guild_id, id__not=self.pk).order_by("reg_start_time")
        if not scrims:
            return

        prompt = await self.bot.prompt(
            target,
            target.user,
            "Do you want to apply this change to all scrims?",
            ephemeral=True,
        )

        if not prompt:
            return

        await Scrim.filter(id__in=[scrim.pk for scrim in scrims]).update(**kwargs)
        await target.followup.send(embed=self.bot.success_embed("Changes applied to all scrims.", title="Success"), ephemeral=True)

    async def setup_logs(self):
        _reason = "Created for scrims management."

        guild = self.guild

        if not (scrims_mod_role := self.scrims_mod_role):
            scrims_mod_role = await guild.create_role(name="scrims-mod", color=self.bot.color, reason=_reason)

        overwrite = self.registration_channel.overwrites_for(guild.default_role)
        overwrite.update(read_messages=True, send_messages=True, read_message_history=True)
        await self.registration_channel.set_permissions(scrims_mod_role, overwrite=overwrite)

        if (scrims_log_channel := self.logs_channel) is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                scrims_mod_role: discord.PermissionOverwrite(read_messages=True),
            }
            scrims_log_channel = await guild.create_text_channel(
                name="quotient-scrims-logs",
                overwrites=overwrites,
                reason=_reason,
                topic="**DO NOT RENAME THIS CHANNEL**",
            )

            note = await scrims_log_channel.send(
                embed=discord.Embed(
                    description=f"If events related to scrims i.e opening registrations or adding roles, "
                    f"etc are triggered, then they will be logged in this channel. "
                    f"Also I have created {scrims_mod_role.mention}, you can give that role to your "
                    f"scrims-moderators. User with {scrims_mod_role.mention} can also send messages in "
                    f"registration channels and they won't be considered as scrims-registration.\n\n"
                    f"`Note`: **Do not rename this channel.**",
                    color=self.bot.color,
                )
            )
            await note.pin()

    async def send_log(
        self, msg: str, title: str = "", color: discord.Color = None, ping_scrims_mod: bool = False, add_contact_btn: bool = True
    ) -> None:
        embed = discord.Embed(color=color or self.bot.color, title=title, description=msg)
        try:
            await self.logs_channel.send(
                content=getattr(self.scrims_mod_role, "mention", "@scrims-mod") if ping_scrims_mod else "",
                embed=embed,
                view=self.bot.contact_support_view() if add_contact_btn else None,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
        except (discord.HTTPException, AttributeError):
            pass


class BaseScrimSlot(BaseDbModel):
    class Meta:
        abstract = True

    id = fields.IntField(primary_key=True, db_index=True)
    num = fields.SmallIntField(null=True)
    leader_id = fields.BigIntField(null=True)
    team_name = fields.CharField(max_length=100, null=True)
    members = ArrayField("BIGINT", default=list)
    drop_location = fields.CharField(max_length=50, null=True)

    @property
    def leader(self):
        return self.bot.get_user(self.leader_id)


class ScrimAssignedSlot(BaseScrimSlot):
    class Meta:
        table = "scrims_assigned_slots"

    jump_url = fields.CharField(max_length=200, null=True)
    assigned_at = fields.DatetimeField(auto_now=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="assigned_slots")

    @property
    def message_id(self):
        return int(self.jump_url.split("/")[-1]) if self.jump_url else None


class ScrimReservedSlot(BaseScrimSlot):
    class Meta:
        table = "scrims_reserved_slots"

    reserved_at = fields.DatetimeField(auto_now=True)
    reserved_by = fields.BigIntField()
    reserved_till = fields.DatetimeField(null=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="reserved_slots")


class ScrimsBannedUser(BaseDbModel):
    class Meta:
        table = "scrims_banned_users"

    id = fields.IntField(primary_key=True)
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()

    reason = fields.CharField(max_length=200, null=True)
    banned_at = fields.DatetimeField(auto_now=True)
    banned_till = fields.DatetimeField(null=True)
    banned_by = fields.BigIntField()

    @property
    def user(self):
        return self.bot.get_user(self.user_id)


class ScrimsBanLog(BaseDbModel):
    class Meta:
        table = "scrims_ban_logs"

    guild_id = fields.BigIntField(primary_key=True, generated=False)
    channel_id = fields.BigIntField()

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)

    async def log_ban(self, banned_user: ScrimsBannedUser) -> None:
        """
        Sends a log message in the banlog channel.
        """
        user: discord.User = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, banned_user.user_id)
        mod = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, banned_user.banned_by)

        e = discord.Embed(color=discord.Color.red(), title=f"🔨 Banned from Scrims", timestamp=self.bot.current_time)
        e.add_field(name="User:", value=f"{user} ({getattr(user, 'mention','`unknown-user`')})")
        e.add_field(name="Banned By:", value=f"{mod} ({getattr(mod, 'mention','`unknown-user`')})")
        e.add_field(
            name="Banned Until:",
            value=discord.utils.format_dt(banned_user.banned_till, "R") if banned_user.banned_till else "`Indefinite`",
        )
        e.add_field(name="Reason:", value=f"```{banned_user.reason or 'No reason given'}```")

        if user:
            e.set_thumbnail(url=getattr(user.display_avatar, "url", "https://cdn.discordapp.com/embed/avatars/0.png"))

        try:
            await self.channel.send(getattr(user, "mention", ""), embed=e)
        except (discord.HTTPException, AttributeError):
            pass

    async def log_unban(self, banned_user: ScrimsBannedUser, unbanned_by: discord.Member | discord.User) -> None:
        """
        Sends a log message in the banlog channel.
        """
        user = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, banned_user.user_id)
        mod = await self.bot.get_or_fetch(self.bot.get_user, self.bot.fetch_user, banned_user.banned_by)

        e = discord.Embed(color=discord.Color.green(), title=f"🍃 Unbanned from Scrims", timestamp=self.bot.current_time)
        e.add_field(name="User:", value=f"{user} ({getattr(user, 'mention','`unknown-user`')})")
        e.add_field(name="Banned By:", value=f"{mod} ({getattr(mod, 'mention','`unknown-user`')})")
        e.add_field(name="Unbanned By:", value=f"{unbanned_by} ({getattr(unbanned_by, 'mention','`unknown-user`')})")
        e.add_field(name="Was Banned For:", value=f"```{banned_user.reason or 'No reason given'}```")

        if user:
            e.set_thumbnail(url=getattr(user.display_avatar, "url", "https://cdn.discordapp.com/embed/avatars/0.png"))

        try:
            await self.channel.send(getattr(user, "mention", ""), embed=e)
        except (discord.HTTPException, AttributeError):
            pass
