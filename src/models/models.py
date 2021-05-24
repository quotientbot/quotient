from attr import field
from .fields import *
from .functions import *
from utils import constants
from tortoise import fields, models
import config, discord

__all__ = ("Guild", "User", "Logging", "Tag", "Timer", "Snipes", "Autorole", "Votes", "Premium", "Redeem", "Stats")


class Guild(models.Model):
    class Meta:
        table = "guild_data"

    guild_id = fields.BigIntField(pk=True, index=True)
    prefix = fields.CharField(default="q", max_length=5)
    embed_color = fields.IntField(default=65459, null=True)
    embed_footer = fields.TextField(default=config.FOOTER)  # i am not sure if its a good idea to insert it by default :c
    bot_master = BigIntArrayField(default=list, index=True)
    mute_role = fields.BigIntField(null=True)
    muted_members = BigIntArrayField(default=list)
    tag_enabled_for_everyone = fields.BooleanField(default=True)  # ye naam maine ni rkha sachi
    emoji_stealer_channel = fields.BigIntField(null=True, index=True)
    emoji_stealer_message = fields.BigIntField(null=True, index=True)
    is_premium = fields.BooleanField(default=False)
    made_premium_by = fields.BigIntField(null=True)
    premium_end_time = fields.DatetimeField(null=True)
    premium_notified = fields.BooleanField(default=False)  # this is useful, I just don't remember where :c
    public_profile = fields.BooleanField(default=True)  # whether to list the server on global leaderboards
    private_channel = fields.BigIntField(null=True, index=True)
    private_webhook = fields.TextField(null=True)
    disabled_channels = BigIntArrayField(default=list, index=True)  # channels where bot won't reply to cmds
    disabled_commands = CharVarArrayField(default=list, index=True)
    disabled_users = BigIntArrayField(default=list, index=True)
    censored = CharVarArrayField(default=list, index=True)  # will shift this to automod

    @property
    def _guild(self):
        return self.bot.get_guild(self.guild_id)

    @property
    def mute_role(self):
        if self._guild is not None:
            return self._guild.get_role(self.mute_role)

    @property
    def private_ch(self):
        if self._guild is not None:
            return self._guild.get_channel(self.private_channel)

    @property
    def muted(self):
        return tuple(map(self.bot.get_user, self.muted_members))

    # ************************************************************************************************


# TODO: make manytomany field in user_data for redeem codes.
class User(models.Model):
    class Meta:
        table = "user_data"

    user_id = fields.BigIntField(pk=True, index=True)
    is_premium = fields.BooleanField(default=False, index=True)
    premium_expire_time = fields.DatetimeField(null=True)
    made_premium = BigIntArrayField(default=list)  # a list of servers this user boosted
    premiums = fields.IntField(default=0)
    premium_notified = fields.BooleanField(default=False)
    public_profile = fields.BooleanField(default=True)
    # badges = CharVarArrayField(default=list)


# ************************************************************************************************


class Logging(models.Model):
    class Meta:
        table = "logging"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField(index=True)
    channel_id = fields.BigIntField()
    color = fields.IntField(default=0x2F3136)  # modlogs m noi
    toggle = fields.BooleanField(default=True)
    ignore_bots = fields.BooleanField(default=False)
    type = fields.CharEnumField(constants.LogType, max_length=12, index=True)

    @property
    def channel(self):
        return self.bot.get_channel(self.channel_id)


# # ************************************************************************************************


class Tag(models.Model):
    class Meta:
        table = "tags"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    name = fields.CharField(max_length=100)
    content = fields.TextField()
    is_embed = fields.BooleanField(default=False)
    is_nsfw = fields.BooleanField(default=False)
    owner_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)
    usage = fields.IntField(default=0)

    @property
    def owner(self):
        return self.bot.get_user(self.owner_id)


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
class Snipes(models.Model):
    class Meta:
        table = "snipes"

    # since it isn't recomended to create index on tables which are updated very frequently,
    # I am not sure if I should create an Index on channel_id :c

    # I have read about it a lot and I learnt a lot too, yes I understand select speed matters with commands like snipe but because,
    # this table is gonna be updated very very frequently, I will not create index here because this will very badly affect the insert,
    # update and delete queries and ultimately the whole database performance.
    # I will leave the above comment as it is with a hope that it might be helpful for anyone reading it.
    id = fields.BigIntField(pk=True)
    author_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    content = fields.TextField()
    delete_time = fields.DatetimeField(auto_now=True)
    nsfw = fields.BooleanField(default=False)

    @property
    def author(self):
        return self.bot.get_user(self.author_id)


# ************************************************************************************************
class Autorole(models.Model):
    class Meta:
        table = "autoroles"

    guild_id = fields.BigIntField(pk=True, index=True)
    humans = BigIntArrayField(default=list)
    bots = BigIntArrayField(default=list)

    @property
    def _guild(self) -> Optional[discord.Guild]:
        return self.bot.get_guild(self.guild_id)

    @property
    def human_roles(self):
        if self._guild is not None:
            return tuple(map(lambda x: getattr(self._guild.get_role(x), "mention", "Deleted"), self.humans))

    @property
    def bot_roles(self):
        if self._guild is not None:
            return tuple(map(lambda x: getattr(self._guild.get_role(x), "mention", "Deleted"), self.bots))


# ************************************************************************************************


class Votes(models.Model):
    class Meta:
        table = "votes"

    user_id = fields.BigIntField(pk=True)
    is_voter = fields.BooleanField(delete=False, index=True)
    expire_time = fields.DatetimeField(null=True)
    reminder = fields.BooleanField(default=False)
    notified = fields.BooleanField(default=False, index=True)
    public_profile = fields.BooleanField(default=True)
    total_votes = fields.IntField(default=0)


# ************************************************************************************************


class Premium(models.Model):
    class Meta:
        table = "premium_logs"

    order_id = fields.CharField(max_length=50, pk=True)
    user_id = fields.BigIntField()
    payment_id = fields.CharField(max_length=50, null=True)
    payment_time = fields.DatetimeField(null=True)
    plan_1 = fields.IntField(default=0, null=True)
    plan_2 = fields.IntField(default=0, null=True)
    plan_3 = fields.IntField(default=0, null=True)
    amount = fields.IntField(default=0, null=True)
    token = fields.TextField(null=True)
    is_done = fields.BooleanField(default=False, null=True)
    order_time = fields.DatetimeField(null=True)
    username = fields.CharField(max_length=200, null=True)
    email = fields.CharField(max_length=200, null=True)
    is_notified = fields.BooleanField(default=False, null=True)


class Redeem(models.Model):
    class Meta:
        table = "redeem_codes"

    user_id = fields.BigIntField()
    code = fields.CharField(max_length=50, pk=True, index=True)
    created_at = fields.DatetimeField(auto_now=True)
    expire_time = fields.DatetimeField()
    is_used = fields.BooleanField(default=False)
    used_by = fields.BigIntField(null=True)
    used_at = fields.DatetimeField(null=True)


# ************************************************************************************************
