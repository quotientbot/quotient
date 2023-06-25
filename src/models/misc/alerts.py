from __future__ import annotations

from tortoise import fields

from models import BaseDbModel
from models.helpers import *


class Alert(BaseDbModel):
    class Meta:
        table = "alerts"

    id = fields.IntField(pk=True)
    author_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)
    active = fields.BooleanField(default=True)
    message = fields.JSONField(default=dict)
    conditions = ArrayField(fields.CharField(max_length=100), default=list)
    prompts: fields.ManyToManyRelation["Prompt"] = fields.ManyToManyField("models.Prompt")
    reads: fields.ManyToManyRelation["Read"] = fields.ManyToManyField("models.Read")


class Prompt(BaseDbModel):
    class Meta:
        table = "alert_prompts"

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    prompted_at = fields.DatetimeField(auto_now=True)


class Read(BaseDbModel):
    class Meta:
        table = "alert_reads"

    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    read_at = fields.DatetimeField(auto_now=True)
