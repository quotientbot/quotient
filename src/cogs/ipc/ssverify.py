from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .base import IpcCog
from discord.ext import ipc

from models import SSVerify


class SSverifyIpc(IpcCog):
    def __init__(self, bot: Quotient):
        self.bot = bot

    @ipc.server.route()
    async def create_ssverify(self, payload):
        data = payload.data

    @ipc.server.route()
    async def edit_ssverify(self, payload):
        data = payload.data

    @ipc.server.route()
    async def delete_ssverify(self, payload):
        await SSVerify.filter(pk=int(payload.id)).delete()
        return self.positive
