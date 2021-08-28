from tortoise import models, fields
from models.helpers import *


class Subscriptions(models.Model):
    class Meta:
        table = "subscriptions"

    guild_id = fields.BigIntField(pk=True)
    log_channel_id = fields.BigIntField()
    slug = fields.CharField(max_length=20)
    balance = fields.IntField(default=0)
    upi_id = fields.CharField(max_length=25)

    plans: fields.ManyToManyRelation["SubPlan"] = fields.ManyToManyField("models.SubPlan")
    logs: fields.ManyToManyRelation["SubLog"] = fields.ManyToManyField("models.SubLog")


class SubPlan(models.Model):
    class Meta:
        table = "subscription_plans"

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=30)
    theme_color = fields.CharField(max_length=7)
    days = fields.IntField(default=1)
    slots = fields.IntField(default=1)
    perks = ArrayField(fields.CharField(max_length=100))
    price = fields.IntField()


class SubLog(models.Model):
    class Meta:
        table = "subscription_logs"

    id = fields.IntField(pk=True)
