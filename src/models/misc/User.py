from tortoise import fields, models

from models.helpers import ArrayField


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
