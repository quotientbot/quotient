from models.helpers import ArrayField
from tortoise import fields ,models



# TODO: make manytomany field in user_data for redeem codes.
class User(models.Model):
    class Meta:
        table = "user_data"

    user_id = fields.BigIntField(pk=True, index=True)
    is_premium = fields.BooleanField(default=False, index=True)
    premium_expire_time = fields.DatetimeField(null=True)
    made_premium = ArrayField(fields.BigIntField(), default=list)  # a list of servers this user boosted
    premiums = fields.IntField(default=0)
    premium_notified = fields.BooleanField(default=False)
    public_profile = fields.BooleanField(default=True)
    # badges = CharVarArrayField(default=list)
    money = fields.IntField(default=0)


# ************************************************************************************************


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


class Votes(models.Model):
    class Meta:
        table = "votes"

    user_id = fields.BigIntField(pk=True)
    is_voter = fields.BooleanField(default=False, index=True)
    expire_time = fields.DatetimeField(null=True)
    reminder = fields.BooleanField(default=False)
    notified = fields.BooleanField(default=False, index=True)
    public_profile = fields.BooleanField(default=True)
    total_votes = fields.IntField(default=0)


# ************************************************************************************************
class Snipe(models.Model):
    class Meta:
        table = "snipes"

    channel_id = fields.BigIntField(pk=True)
    author_id = fields.BigIntField()
    content = fields.TextField()
    delete_time = fields.DatetimeField(auto_now=True)
    nsfw = fields.BooleanField(default=False)

    @property
    def author(self):
        return self.bot.get_user(self.author_id)