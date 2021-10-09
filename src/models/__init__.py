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


from .models import *
from .esports import *
from .misc import *

from .helpers import *
