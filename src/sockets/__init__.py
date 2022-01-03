from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

from .app import init_application
from core import Cog

from socketio import AsyncClient


class SocketConnection(Cog):
    connected: bool = False
    sio: AsyncClient

    def __init__(self, bot: Quotient):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.__make_connection())

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.__close_connection())

    async def __make_connection(self):
        self.sio = await init_application()
        self.connected = True

    async def __close_connection(self):
        if self.connected:
            print("Closing Server")
            await self.sio.disconnect()

            self.task.cancel()


def setup(bot: Quotient):
    bot.add_cog(SocketConnection(bot))
