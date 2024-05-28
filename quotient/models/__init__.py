from __future__ import annotations

from typing import TYPE_CHECKING

from tortoise import models


class BaseDbModel(models.Model):
    """Base Model for all tortoise models"""

    if TYPE_CHECKING:
        from core import Quotient

    bot: Quotient

    class Meta:
        abstract = True


from .esports import *
from .others import *
