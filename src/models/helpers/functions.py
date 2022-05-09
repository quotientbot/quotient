import typing
from enum import Enum

from pypika.terms import Function
from tortoise.expressions import F

__all__ = (
    "ArrayAppend",
    "ArrayRemove",
)


class ArrayAppend(Function):
    def __init__(self, field: str, value: typing.Any) -> None:
        if isinstance(value, Enum):
            value = value.value

        super().__init__("ARRAY_APPEND", F(field), str(value))


class ArrayRemove(Function):
    def __init__(self, field: str, value: typing.Any) -> None:
        if isinstance(value, Enum):
            value = value.value

        super().__init__("ARRAY_REMOVE", F(field), str(value))
