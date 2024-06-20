import asyncio

import discord
from models import BaseDbModel
from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField

from ..others import Timer
from .enums import Day, IdpShareType


class Scrim(BaseDbModel):

    class Meta:
        table = "scrims"

    id = fields.IntField(primary_key=True, db_index=True)

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

    registration_open_days = ArrayField("SMALLINT", default=lambda: list([day.value for day in Day]))

    slotlist_msg_design = fields.JSONField(default=dict)
    open_msg_design = fields.JSONField(default=dict)
    close_msg_design = fields.JSONField(default=dict)

    reactions = ArrayField("VARCHAR(50)", default=lambda: list(["✅", "❌"]))
    required_lines = fields.SmallIntField(default=0)
    scrim_status = fields.BooleanField(default=True)

    slot_reminders: fields.ReverseRelation["ScrimSlotReminder"]
    assigned_slots: fields.ReverseRelation["ScrimAssignedSlot"]
    reserved_slots: fields.ReverseRelation["ScrimReservedSlot"]
    banned_teams: fields.ReverseRelation["ScrimBannedTeam"]

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
        await ScrimBannedTeam.filter(scrim_id=self.id).delete()
        await ScrimSlotReminder.filter(scrim_id=self.id).delete()
        await self.delete()

    @property
    def registration_open_embed(self):
        reserved_slots_count = len(self.reserved_slots)

        if len(self.open_msg_design) <= 1:
            return discord.Embed(
                color=self.bot.color,
                title="Registration is now open!",
                description=f"📣 **`{self.required_mentions}`** mentions required.\n"
                f"📣 Total slots: **`{self.total_slots}`** [`{reserved_slots_count}` slots reserved]",
            )

        # TODO: custom open msg

    @property
    def registration_close_embed(self):
        if len(self.close_msg_design) <= 1:
            return discord.Embed(color=self.bot.color, description="**Registration is now Closed!**")

    async def refresh_timers(self):
        """
        Delete the timers and create new ones.
        """

        await Timer.filter(
            extra={"args": [], "kwargs": {"scrim_id": self.id}},
            event__in=["scrim_reg_start", "scrim_reg_end", "scrim_channel_autoclean"],
        ).delete()

        await self.bot.reminders.create_timer(self.reg_start_time, "scrim_reg_start", scrim_id=self.id)
        if self.reg_auto_end_time:
            await self.bot.reminders.create_timer(self.reg_auto_end_time, "scrim_reg_end", scrim_id=self.id)
        if self.autoclean_channel_time:
            await self.bot.reminders.create_timer(self.autoclean_channel_time, "scrim_channel_autoclean", scrim_id=self.id)

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

        self.started_at = self.bot.current_time
        self.ended_at = None
        self.slotlist_message_id = None

        await self.save(update_fields=["started_at", "ended_at", "slotlist_message_id", "available_slots"])
        await asyncio.sleep(0.2)

        self.bot.cache.scrim_channel_ids.add(self.registration_channel_id)

        await self.registration_channel.send(
            getattr(self.start_ping_role, "mention", ""),
            embed=self.registration_open_embed,
            allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
        )

        # TODO: send to logs channel
        from lib import toggle_channel_perms

        await toggle_channel_perms(self.registration_channel, self.open_role, True)

    async def close_registration(self):

        self.ended_at = self.bot.current_time
        self.registration_time_elapsed = (self.ended_at - self.started_at).total_seconds()
        self.started_at = None

        await self.save(update_fields=["ended_at", "registration_time_elapsed", "started_at"])

        from lib import toggle_channel_perms

        registration_channel = self.registration_channel
        await toggle_channel_perms(registration_channel, self.open_role, False)

        try:
            await registration_channel.send(
                getattr(self.end_ping_role, "mention", ""),
                embed=self.registration_close_embed,
                allowed_mentions=discord.AllowedMentions(everyone=True, roles=True),
            )
        except discord.HTTPException:
            pass

        # TODO: send to logs channel

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


class ScrimSlotReminder(BaseDbModel):
    class Meta:
        table = "scrims_slot_reminders"

    id = fields.IntField(primary_key=True)
    user_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="slot_reminders")


class BaseScrimSlot(BaseDbModel):
    class Meta:
        abstract = True

    id = fields.IntField(primary_key=True, db_index=True)
    num = fields.SmallIntField(null=True)
    leader_id = fields.BigIntField(null=True)
    team_name = fields.CharField(max_length=100, null=True)
    members = ArrayField("BIGINT", default=list)

    @property
    def leader(self):
        return self.bot.get_user(self.leader_id)


class ScrimAssignedSlot(BaseScrimSlot):
    class Meta:
        table = "scrims_assigned_slots"

    jump_url = fields.CharField(max_length=200, null=True)
    assigned_at = fields.DatetimeField(auto_now=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="assigned_slots")


class ScrimReservedSlot(BaseScrimSlot):
    class Meta:
        table = "scrims_reserved_slots"

    reserved_at = fields.DatetimeField(auto_now=True)
    reserved_by = fields.BigIntField()
    reserved_till = fields.DatetimeField(null=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="reserved_slots")


class ScrimBannedTeam(BaseScrimSlot):
    class Meta:
        table = "scrims_banned_teams"

    reason = fields.CharField(max_length=200, null=True)
    banned_at = fields.DatetimeField(auto_now=True)
    banned_till = fields.DatetimeField(null=True)
    banned_by = fields.BigIntField()

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="banned_teams")