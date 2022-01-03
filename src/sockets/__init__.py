from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient
from core import Cog

from socketio import AsyncClient

from .app import sio


class SocketConnection(Cog):
    connected: bool = False
    sio: AsyncClient

    def __init__(self, bot: Quotient):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.__make_connection())

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.__close_connection())

    async def __make_connection(self):
        await sio.connect("http://1ba6-203-187-194-194.ngrok.io/api/", auth={"token": self.bot.config.SOCKET_AUTH})

        self.connected = True

    async def __close_connection(self):
        if self.connected:
            print("Closing Server")
            await sio.disconnect()

            self.task.cancel()


def setup(bot: Quotient):
    bot.add_cog(SocketConnection(bot))
