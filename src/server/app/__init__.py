from typing import Tuple

from aiohttp import web
from aiohttp_asgi import ASGIResource

from .app import app

__all__ = ("init_application",)


async def init_application() -> Tuple[web.Application, web.TCPSite]:
    aiohttp_app = web.Application()
    asgi_resource = ASGIResource(app, root_path="/")  # type: ignore
    aiohttp_app.router.register_resource(asgi_resource)

    runner = web.AppRunner(app=aiohttp_app)
    await runner.setup()
    webserver = web.TCPSite(runner, "0.0.0.0", 8888)
    await webserver.start()
    print("Asgi server started")
    return aiohttp_app, webserver
