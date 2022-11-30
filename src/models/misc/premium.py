from models import BaseDbModel
from tortoise import fields


class PremiumPlan(BaseDbModel):
    class Meta:
        table = "premium_plans"

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50)
    description = fields.CharField(max_length=250)
    price = fields.IntField()
    duration = fields.TimeDeltaField()


class PremiumPurchase(BaseDbModel):
    class Meta:
        table = "premium_purchases"

    id = fields.IntField(pk=True)
    txnid = fields.CharField(max_length=100)
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()
    plan_id = fields.IntField()

    created_at = fields.DatetimeField(auto_now=True)
    completed_at = fields.DatetimeField(null=True)
    raw_data = fields.JSONField(default=dict)
