from models import BaseDbModel
from tortoise import fields
from tortoise.contrib.postgres.fields import ArrayField

from .enums import Day


class Scrim(BaseDbModel):
    class Meta:
        table = "scrims"

    id = fields.IntField(primary_key=True, db_index=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=100)
    registration_channel_id = fields.BigIntField(db_index=True)

    slotlist_channel_id = fields.BigIntField()
    slotlist_message_id = fields.BigIntField(null=True)
    slotlist_start_from = fields.SmallIntField(default=1)
    autosend_slotlist = fields.BooleanField(default=True)

    required_mentions = fields.SmallIntField(default=4)

    available_slots = ArrayField("SMALLINT", default=list)
    total_slots = fields.SmallIntField()

    start_time = fields.DatetimeField()
    started_at = fields.DatetimeField(null=True)
    ended_at = fields.DatetimeField(null=True)

    autoclean_channel = fields.BooleanField(default=True)
    autoclean_role = fields.BooleanField(default=True)
    autoclean_time = fields.DatetimeField(null=True)

    success_role_id = fields.BigIntField()
    reg_start_ping_role_id = fields.BigIntField(null=True)
    reg_end_ping_role_id = fields.BigIntField(null=True)
    open_role_id = fields.BigIntField(null=True)

    allow_multiple_registrations = fields.BooleanField(default=True)
    autodelete_rejected_registrations = fields.BooleanField(default=False)
    autodelete_extra_msges = fields.BooleanField(default=False)
    allow_without_teamname = fields.BooleanField(default=False)
    allow_duplicate_teamname = fields.BooleanField(default=True)
    allow_duplicate_mentions = fields.BooleanField(default=False)

    registration_time_elapsed = fields.SmallIntField(default=0)  # in seconds
    show_registration_time_elapsed = fields.BooleanField(default=True)

    registration_open_days = ArrayField("SMALLINT", default=lambda: list([day.value for day in Day]))

    slotlist_msg_design = fields.JSONField(default=dict)
    open_msg_design = fields.JSONField(default=dict)
    close_msg_design = fields.JSONField(default=dict)

    reactions = ArrayField("VARCHAR(50)", default=list)
    required_lines = fields.SmallIntField(default=0)
    scrim_status = fields.BooleanField(default=True)

    slot_reminders: fields.ReverseRelation["ScrimSlotReminder"]
    assigned_slots: fields.ReverseRelation["AssignedSlot"]
    reserved_slots: fields.ReverseRelation["ReservedSlot"]
    banned_teams: fields.ReverseRelation["BannedTeam"]


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
    leader_id = fields.BigIntField()
    team_name = fields.CharField(max_length=100, null=True)
    members = ArrayField("BIGINT", default=list)

    @property
    def leader(self):
        return self.bot.get_user(self.leader_id)


class AssignedSlot(BaseScrimSlot):
    class Meta:
        table = "scrims_assigned_slots"

    message_id = fields.BigIntField(null=True)
    jump_url = fields.CharField(max_length=200, null=True)
    assigned_at = fields.DatetimeField(auto_now=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="assigned_slots")


class ReservedSlot(BaseScrimSlot):
    class Meta:
        table = "scrims_reserved_slots"

    reserved_at = fields.DatetimeField(auto_now=True)
    reserved_by = fields.BigIntField()
    reserved_till = fields.DatetimeField(null=True)

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="reserved_slots")


class BannedTeam(BaseScrimSlot):
    class Meta:
        table = "scrims_banned_teams"

    reason = fields.CharField(max_length=200, null=True)
    banned_at = fields.DatetimeField(auto_now=True)
    banned_till = fields.DatetimeField(null=True)
    banned_by = fields.BigIntField()

    scrim: fields.ForeignKeyRelation[Scrim] = fields.ForeignKeyField("default.Scrim", related_name="banned_teams")
