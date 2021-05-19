from .fields import *
from .functions import *
from utils.constants import Day, LogType
from tortoise import fields, models
import discord, config


# class Guild(models.Model):
#     class Meta:
#         table = "guild_data"

#     guild_id = fields.BigIntField(pk=True)
#     prefix = fields.CharField(default="q")
#     embed_color = fields.IntField(default=65459)
#     embed_footer = fields.TextField(
#         default=config.FOOTER
#     )  # i am not sure if its a good idea to insert it by default :c
#     bot_master = BigIntArrayField(
#         default=list
#     )  # they can use all quo cmds even if they don't have required permissions
#     mute_role = fields.BigIntField(null=True)
#     muted_members = BigIntArrayField(default=list)
#     tag_enabled_for_everyone = fields.BooleanField(
#         default=True
#     )  # ye naam maine ni rkha sachi
#     emoji_stealer_channel = fields.BigIntField(null=True)
#     emoji_stealer_message = fields.BigIntField(null=True)
#     is_premium = fields.BooleanField(default=False)
#     made_premium_by = fields.BigIntField(null=True)
#     premium_end_time = fields.DatetimeField(null=True)
#     premium_notified = fields.BooleanField(
#         default=False
#     )  # this is useful, I just don't remember where :c
#     public_profile = fields.BooleanField(
#         default=True
#     )  # whether to list the server on global leaderboards
#     private_channel = fields.BigIntField(null=True)
#     private_webhook = fields.TextField(null=True)
#     disabled_channels = BigIntArrayField(
#         default=list
#     )  # channels where bot won't reply to cmds
#     disabled_commands = CharVarArrayField(default=list)
#     disabled_users = BigIntArrayField(default=list)
#     censored = CharVarArrayField(default=list)  # will shift this to automod

#     @property
#     def obj(self):  # Guild.guild utna acha nai lgta :c
#         return self.bot.get_guild(self.guild_id)

#     @property
#     def mute_role(self):
#         if self.guild is not None:
#             return self.guild.get_role(self.mute_role)

#     @property
#     def muted_members(self):
#         return list(map(self.bot.get_user, self.muted_members))

#     # ************************************************************************************************


# class User(models.Model):
#     class Meta:
#         table = "user_data"

#     user_id = fields.BigIntField(pk=True)
#     is_premium = fields.BooleanField(default=False)
#     premium_expire_time = fields.DatetimeField(null=True)
#     made_premium = BigIntArrayField(default=list)  # a list of servers this user boosted
#     premiums = fields.IntField(default=0)
#     premium_notified = fields.BooleanField(default=False)
#     public_profile = fields.BooleanField(default=True)
#     badges = CharVarArrayField(default=list)

#     @property
#     def obj(self):
#         return self.bot.get_user(self.user_id)


# # ************************************************************************************************


# class Logging(models.Model):
#     class Meta:
#         table = "logging"

#     id = fields.BigIntField(pk=True)
#     guild_id = fields.BigIntField()
#     channel_id = fields.BigIntField()
#     color = fields.IntField()  # modlogs m noi
#     toggle = fields.BooleanField(default=True)
#     ignore_bots = fields.BooleanField(default=False)
#     ignored_channels = BigIntArrayField(default=list)
#     type = fields.CharEnumField(LogType)

#     @property
#     def channel(self):
#         return self.bot.get_channel(self.channel_id)


# # ************************************************************************************************


# class Tag(models.Model):
#     class Meta:
#         table = "tags"

#     id = fields.BigIntField(pk=True)
#     guild_id = fields.BigIntField()
#     name = fields.CharField()
#     content = fields.TextField()
#     is_embed = fields.BooleanField(default=False)
#     is_nsfw = fields.BooleanField(default=False)
#     owner_id = fields.BigIntField()
#     created_at = fields.DatetimeField(auto_now=True)
#     usage = fields.IntField(default=0)

#     @property
#     def owner(self):
#         return self.bot.get_user(self.owner_id)


# ************************************************************************************************

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
    slotlist_message_id = fields.BigIntField(null=True)
    role_id = fields.BigIntField(null=True)
    required_mentions = fields.IntField()
    total_slots = fields.IntField()
    host_id = fields.BigIntField()
    open_time = fields.DatetimeField()
    opened_at = fields.DatetimeField(null=True)
    closed_at = fields.DatetimeField(null=True)
    autoclean = fields.BooleanField(default=False)
    autoslotlist = fields.BooleanField(default=True)
    ping_role_id = fields.BigIntField(null=True)
    stoggle = fields.BooleanField(default=True)
    open_role_id = fields.BigIntField(null=True)
    open_days = EnumArrayField(Day, default=Day.__iter__)
    assigned_slots: fields.ManyToManyRelation["AssignedSlot"] = fields.ManyToManyField("models.AssignedSlot")
    reserved_slots: fields.ManyToManyRelation["ReservedSlot"] = fields.ManyToManyField("models.ReservedSlot")
    banned_teams: fields.ManyToManyRelation["BannedTeam"] = fields.ManyToManyField("models.BannedTeam")

    @property
    def guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def role(self):
        if self.guild is not None:
            return self.guild.get_role(self.role_id)

    @property
    def logschan(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.text_channels, name="quotient-scrims-logs")

    @property
    def modrole(self):
        if self.guild is not None:
            return discord.utils.get(self.guild.roles, name="scrims-mod")

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
        return list(map(self.bot.get_user, self.banned_users_ids()))

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
            if self.open_role_id is not None:
                return self.guild.get_role(self.open_role_id)
            else:
                return self.guild.default_role

    @property  # what? you think its useless , i know :)
    def toggle(self):
        return self.stoggle

    @property
    def teams_registered(self):  # This should be awaited
        return self.assigned_slots.order_by("num").all()

    async def user_registered(self):
        async for members in self.teams_registered.only("members"):
            for member_id in members:
                yield member_id

    async def reserved_user_ids(self):
        return (i.user_id for i in await self.reserved_slots.all())

    async def banned_user_ids(self):
        return (i.user_id for i in await self.banned_teams.all())

    async def create_slotlist(self):
        slots = await self.teams_registered
        description = "\n".join(f"Slot {slot.num:02}  ->  {slot.team_name}" for slot in slots)
        embed = discord.Embed(title=self.name + " Slotlist", description=f"```{description}```")
        channel = self.slotlist_channel
        return embed, channel


class BaseSlot(models.Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    team_name = fields.TextField(null=True)
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


class BannedTeam(BaseSlot):
    class Meta:
        table = "sm.banned_teams"

    expires = fields.DatetimeField(null=True)


# ************************************************************************************************


# class Fornite(models.Model):
#     class Meta:
#         table = "fn.settings"

#     guild_id = fields.BigIntField(pk=True)
#     suspended_role_id = fields.BigIntField()
#     yunite_api_key = fields.TextField()
#     logging_channel_id = fields.BigIntField()
#     logging_toggle = fields.BooleanField(default=True)
#     data = fields.ManyToManyField("models.ForData")

#     @property
#     def guild(self):
#         return self.bot.get_guild(self.guild_id)

#     @property
#     def suspended_role(self):
#         if self.guild is not None:
#             return self.guild.get_role(self.suspended_role_id)

#     @property
#     def logging_channel(self):
#         if self.guild is not None:
#             return self.guild.get_channel(self.logging_channel_id)


# class ForData(models.Model):
#     class Meta:
#         table = "fn.data"

#     id = fields.BigIntField(pk=True)
#     moderator_id = fields.BigIntField()
#     action_user_id = fields.BigIntField()
#     start_time = fields.DatetimeField(auto_now=True)
#     expire_time = fields.DatetimeField()
#     reason = fields.TextField(null=True)
#     jump_url = fields.TextField(null=True)

# ************************************************************************************************
