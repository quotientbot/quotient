from enum import IntEnum

from tortoise import fields

from models import BaseDbModel

__all__ = ("BlockList", "BlockIdType")


class BlockIdType(IntEnum):
    USER = 1
    GUILD = 2


class BlockList(BaseDbModel):
    class Meta:
        table = "block_list"

    id = fields.IntField(pk=True)
    block_id = fields.BigIntField()
    block_id_type = fields.IntEnumField(BlockIdType)
    blocked_by = fields.BigIntField(null=True)
    reason = fields.CharField(max_length=250, null=True)
    timestamp = fields.DatetimeField(auto_now=True)
