from __future__ import annotations

import typing as T

if T.TYPE_CHECKING:
    from core import Quotient

import os

from aiohttp import web
from aiohttp_asgi import ASGIResource
from discord.ext import commands

from .app import fastapi_app


class PremiumPaymentServer(commands.Cog):
    app: web.Application
    app_started: bool = False
    webserver: web.TCPSite

    def __init__(self, bot: Quotient):
        self.bot = bot

    async def cog_load(self) -> None:
        self.app, self.webserver = await self.init_application()
        self.app_started = True

    async def cog_unload(self) -> None:
        if self.app_started:
            self.bot.logger.info("Stopping ASGI server...")

            await self.webserver.stop()
            await self.app.shutdown()
            await self.app.cleanup()

    async def init_application(self) -> T.Tuple[web.Application, web.TCPSite]:
        aiohttp_app = web.Application(logger=self.bot.logger)
        asgi_resource = ASGIResource(fastapi_app, root_path="")  # type: ignore
        aiohttp_app.router.register_resource(asgi_resource)

        runner = web.AppRunner(app=aiohttp_app)
        await runner.setup()
        webserver = web.TCPSite(
            runner,
            "0.0.0.0",
            os.getenv("PAYMENT_SERVER_PORT"),
        )
        await webserver.start()
        self.bot.logger.info("ASGI server started.")
        return aiohttp_app, webserver


async def setup(bot: Quotient):
    await bot.add_cog(PremiumPaymentServer(bot))