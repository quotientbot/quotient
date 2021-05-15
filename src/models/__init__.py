from .fields import BigIntArrayField, EnumArrayField
from utils.constants import Day
from tortoise import fields, models

# ************************************************************************************************
class Timer(models.Model):
    id = fields.BigIntField(pk=True)
    expires = fields.DatetimeField(index=True)
    created = fields.DatetimeField(auto_now=True)
    event = fields.TextField()
    extra = fields.JSONField(default=dict)

    @property
    def kwargs(self):
        return self.extra.get("kwargs", {})

    @property
    def args(self):
        return self.extra.get("args", ())


# ************************************************************************************************


class Scrim(models.Model):
    class Meta:
        table = "sm.scrims"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    name = fields.TextField(default="Quotient-Scrims")
    registration_channel_id = fields.BigIntField()
    slotlist_channel_id = fields.BigIntField()
    slotlist_sent = fields.BooleanField(default=False)
    slotlist_message_id = fields.BigIntField(null=True)
    role_id = fields.BigIntField(null=True)
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    host_id = fields.BigIntField()
    banned_users_ids = BigIntArrayField(default=list)
    open_time = fields.DatetimeField()
    opened_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    autoclean = fields.BooleanField(default=False)
    ping_role_id = fields.BigIntField(null=True)
    stoggle = fields.BooleanField(default=True)
    open_role_id = fields.BigIntField(null=True)
    open_days = EnumArrayField(Day, default=lambda: list(Day))
    assigned_slots = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField(
        "models.ReservedSlot"
    )

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def registration_channel(self):
        return self.bot.get_channel(self.registration_channel_id)

    @property
    def slotlist_channel(self):
        return self.bot.get_channel(self.slotlist_channel_id)

    @property
    def host(self):
        if self.guild is not None:
            return self.guild.get_member(self.host_id)

        return self.bot.get_user(self.host_id)

    @property
    def banned_users(self):
        return list(map(self.bot.get_user, self.banned_users_ids))

    @property
    def opened(self):
        if self.opened_at is None:
            return False

        if self.closed_at is not None:
            return self.closed_at < self.opened_at

        return True

    @property
    def closed(self):
        return not self.opened

    @property
    def ping_role(self):
        if self.guild is not None:
            return self.guild.get_role(self.ping_role_id)

    @property
    def open_role(self):
        if self.guild is not None:
            return self.guild.get_role(self.open_role_id)

    @property  # what? you think its useless , i know :)
    def toggle(self):
        return self.stoggle

    @property
    def teams_registered(self):  # This should be awaited
        return self.assinged_slots.all()

    async def user_registered(self):
        async for members in self.teams_registered.only("members"):
            for member_id in members:
                yield member_id


# ************************************************************************************************


class BaseSlot(models.Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    team_name = fields.TextField()
    members = BigIntArrayField(default=list)


class AssignedSlot(BaseSlot):
    class Meta:
        table = "sm.assigned_slots"

    num = fields.IntField()
    jump_url = fields.TextField(null=True)


class ReservedSlot(BaseSlot):
    class Meta:
        table = "sm.reserved_slots"

    expires = fields.DatetimeField(null=True)


# ************************************************************************************************
