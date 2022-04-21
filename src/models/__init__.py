from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from tortoise import models


class BaseDbModel(models.Model):
    """Base Model for all tortoise models"""
    class Meta:
        abstract = True

    bot: Quotient


from .models import *  # noqa: F401, F403
from .esports import *  # noqa: F401, F403
from .misc import *  # noqa: F401, F403
from .helpers import *  # noqa: F401, F403
