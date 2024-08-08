import json
from datetime import timedelta
from enum import IntEnum

import httpx
from tortoise import fields

from quotient.models import BaseDbModel


class CurrencyType(IntEnum):
    INR = 1
    USD = 2


class GuildTier(IntEnum):
    FREE = 0
    STARTER = 1
    INTERMEDIATE = 2
    ULTIMATE = 3


INR_PREMIUM_PLANS = [
    {
        "tier": GuildTier.STARTER,
        "price_per_month": 1,
        "price_per_year": 999,
        "emote": "<:B_SYMBOL:1269436552778354851>",
        "description": "Basic features to get you started.",
        "durations": {"month": timedelta(days=28), "year": timedelta(days=365)},
    },
    {
        "tier": GuildTier.INTERMEDIATE,
        "price_per_month": 149,
        "price_per_year": 1599,
        "emote": "<:I_SYMBOL:1269436053383680042>",
        "description": "Advanced tools for growing communities.",
        "durations": {"month": timedelta(days=28), "year": timedelta(days=365)},
    },
    {
        "tier": GuildTier.ULTIMATE,
        "price_per_month": 169,
        "price_per_year": 1999,
        "emote": "<a:diamond:899295009289949235>",
        "description": "All-inclusive access for power users.",
        "durations": {"month": timedelta(days=28), "year": timedelta(days=365)},
    },
    {
        "tier": GuildTier.ULTIMATE,
        "price_lifetime": 4999,
        "emote": "<a:PandaReeRun:929077838273974279>",
        "description": "Lifetime access for dedicated communities.",
        "durations": {"lifetime": timedelta(days=365 * 69)},  # Lifetime duration example
    },
]

USD_PREMIUM_PLANS = [
    {
        "tier": GuildTier.STARTER,
        "price_per_month": 2.99,
        "price_per_year": 35.99,
    },
    {
        "tier": GuildTier.INTERMEDIATE,
        "price_per_month": 4.99,
        "price_per_year": 59.99,
    },
    {
        "tier": GuildTier.ULTIMATE,
        "price_per_month": 5.99,
        "price_per_year": 69.99,
    },
    {
        "tier": GuildTier.ULTIMATE,
        "price_lifetime": 119.99,
    },
]


class PremiumTxn(BaseDbModel):
    class Meta:
        table = "premium_txns"

    txnid = fields.UUIDField(primary_key=True)
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField()

    amount = fields.FloatField()
    currency = fields.IntEnumField(CurrencyType)
    tier = fields.IntEnumField(GuildTier)
    premium_duration = fields.TimeDeltaField()

    created_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)
    raw_data = fields.JSONField(default=dict)

    queue: fields.ReverseRelation["PremiumQueue"]

    async def copy_to_main(self):
        await self.bot.quotient_pool.execute(
            """
            INSERT INTO premium_txns (
                txnid,
                user_id,
                guild_id,
                amount,
                currency,
                tier,
                premium_duration,
                created_at,
                completed_at,
                raw_data
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (txnid)
            DO NOTHING
            """,
            self.txnid,
            self.user_id,
            self.guild_id,
            self.amount,
            self.currency.value,
            self.tier.value,
            int(self.premium_duration.total_seconds() * 1_000_000),
            self.created_at,
            self.completed_at,
            json.dumps(self.raw_data),
        )


class PremiumQueue(BaseDbModel):
    class Meta:
        table = "premium_queue"

    id = fields.IntField(primary_key=True)
    txn: fields.ForeignKeyRelation[PremiumTxn] = fields.ForeignKeyField("default.PremiumTxn", related_name="queue")
    guild_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now_add=True)

    async def copy_premium_to_pro(self):

        await self.bot.pro_pool.execute(
            """
            INSERT INTO premium_txns (
                txnid,
                user_id,
                guild_id,
                amount,
                currency,
                tier,
                premium_duration,
                created_at,
                completed_at,
                raw_data
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (txnid)
            DO NOTHING
            """,
            self.txn.txnid,
            self.txn.user_id,
            self.guild_id,
            self.txn.amount,
            self.txn.currency.value,
            self.txn.tier.value,
            int(self.txn.premium_duration.total_seconds() * 1_000_000),
            self.txn.created_at,
            self.txn.completed_at,
            json.dumps(self.txn.raw_data),
        )

        await self.bot.pro_pool.execute(
            """
            INSERT INTO premium_queue (
                id,
                txn_id,
                guild_id,
                created_at
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id)
            DO NOTHING
            """,
            self.id,
            self.txn.txnid,
            self.guild_id,
            self.created_at,
        )
