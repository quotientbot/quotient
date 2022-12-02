from models import BaseDbModel
from datetime import timedelta
from tortoise import fields
import os

__all__ = ("PremiumTxn", "PremiumPlan")


class PremiumPlan(BaseDbModel):
    class Meta:
        table = "premium_plans"

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50)
    description = fields.CharField(max_length=250, null=True)
    price = fields.IntField()
    duration = fields.TimeDeltaField()

    @staticmethod
    async def insert_plans():
        await PremiumPlan.create(name="Trial", price=29, duration=timedelta(days=7))
        await PremiumPlan.create(name="Basic", price=79, duration=timedelta(days=28))
        await PremiumPlan.create(name="Professional", price=199, duration=timedelta(days=84))
        await PremiumPlan.create(name="GodLike", price=4999, duration=timedelta(days=9999))


class PremiumTxn(BaseDbModel):
    class Meta:
        table = "premium_txns"

    id = fields.IntField(pk=True)
    txnid = fields.CharField(max_length=100)
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()
    plan_id = fields.IntField()

    created_at = fields.DatetimeField(auto_now=True)
    completed_at = fields.DatetimeField(null=True)
    raw_data = fields.JSONField(default=dict)

    @staticmethod
    async def gen_txnid() -> str:
        txnid = None

        while txnid == None:
            _id = "QP_" + os.urandom(16).hex()
            if not await PremiumTxn.filter(txnid=_id).exists():
                txnid = _id

        return txnid
