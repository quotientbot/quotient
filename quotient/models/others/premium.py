import os
from datetime import timedelta
from enum import IntEnum

from models import BaseDbModel
from tortoise import fields

__all__ = ("PremiumTxn", "PremiumPlan")


class Currency(IntEnum):
    INR = 1
    USD = 2


class PremiumPlan(BaseDbModel):
    class Meta:
        table = "premium_plans"

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50)
    description = fields.CharField(max_length=250, null=True)
    price = fields.IntField()
    currency = fields.IntEnumField(Currency, default=Currency.INR)
    duration = fields.TimeDeltaField()

    @staticmethod
    async def insert_plans():
        await PremiumPlan.all().delete()

        await PremiumPlan.create(
            name="Basic (1m)",
            description="Duration: 28 days",
            price=99,
            duration=timedelta(days=28),
        )
        await PremiumPlan.create(
            name="Standard (3m)",
            description="Duration: 84 days",
            price=249,
            duration=timedelta(days=84),
        )
        await PremiumPlan.create(
            name="Advanced (6m)",
            description="Duration: 168 days",
            price=499,
            duration=timedelta(days=168),
        )
        await PremiumPlan.create(
            name="Ultimate (Lifetime)",
            description="Duration: 69 years",
            price=4999,
            duration=timedelta(days=25185),
        )

        await PremiumPlan.create(
            name="Elite (12m)",
            description="Duration: 365 days",
            price=59,
            duration=timedelta(days=365),
            currency=Currency.USD,
        )

        await PremiumPlan.create(
            name="Ultimate (Lifetime)",
            description="Duration: 69 years",
            price=99,
            duration=timedelta(days=25185),
            currency=Currency.USD,
        )


class PremiumTxn(BaseDbModel):
    class Meta:
        table = "premium_txns"

    id = fields.IntField(primary_key=True)
    txnid = fields.CharField(max_length=100)
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()
    plan_id = fields.IntField()

    created_at = fields.DatetimeField(auto_now=True)
    completed_at = fields.DatetimeField(null=True)
    raw_data = fields.JSONField(default=dict)

    @staticmethod
    async def generate_txnid() -> str:
        """
        Generates a unique transaction id for premium transactions.
        """
        txnid = None

        while txnid == None:
            _id = "QP_" + os.urandom(16).hex()
            if not await PremiumTxn.filter(txnid=_id).exists():
                txnid = _id

        return txnid
