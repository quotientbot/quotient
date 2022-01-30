from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import Quotient

from core import Cog
from .app import init_application
from aiohttp import web


class StartServer(Cog):
    app: web.Application
    app_started: bool = False
    webserver: web.TCPSite

    def __init__(self, bot: Quotient) -> None:
        self.bot = bot
        self.task = bot.loop.create_task(self.start_application())

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.close_application())

    async def start_application(self):
        self.app, self.webserver = await init_application()
        self.app_started = True

    async def close_application(self):
        if self.app_started:
            print("Closing server")
            await self.webserver.stop()
            await self.app.shutdown()
            await self.app.cleanup()
            self.task.cancel()


def setup(bot):
    bot.add_cog(StartServer(bot))
