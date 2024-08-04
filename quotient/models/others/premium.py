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
        "price_per_month": 99,
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


class PremiumPlan(BaseDbModel):
    class Meta:
        # table = "premium_plans"
        abstract = True


class PremiumTxn(BaseDbModel):
    class Meta:
        # table = "premium_txns"
        abstract = True

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

    @staticmethod
    async def generate_qr():
        URL = "https://info.payu.in/merchant/postservice.php"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "command": "generate_dynamic_bharat_qr",
            "key": "vDy3i7",
            "hash": "87617bd37d7f2d627c5117ce0f1a97839200870c3281764bad542c90fc9684a2e2108257dfebbb32cfc4c2a83aa4b9bfe7761da745b14b3df2525e75a4eb6846",
            "var1": '{"transactionId":"DBQR1981","transactionAmount":"1","merchantVpa":"gauravdua1.payu@indus","expiryTime":"3600","qrName":"payu","qrCity":"Gurgaon","qrPinCode":"122001","customerName":"Ravi","customerCity":"Ranchi","customerPinCode":"834001","customerPhone":"7800078000","customerEmail":"hello@payu.in","customerAddress":"Ggn","udf3":"deliveryboy1","udf4":"sector14","udf5":"cod","outputType":"string"}',
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(URL, data=payload, headers=headers)
            print(response.text)
