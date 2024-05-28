from core import Quotient
from tortoise import models


class BaseDbModel(models.Model):
    """Base Model for all tortoise models"""

    class Meta:
        abstract = True

    bot: Quotient


from .esports import *
from .others import *
