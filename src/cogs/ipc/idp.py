from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .base import IpcCog


class IdpIpc(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot
