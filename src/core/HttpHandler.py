import config
from aiohttp import web
from .route_helper import get_quo_partners, update_guild_cache, send_idp, create_new_scrim, edit_a_scrim, delete_a_scrim


routes = web.RouteTableDef()


def validator(request):
    token = request.headers.get("access_token", "fake")
    if not token == config.IPC_KEY:
        return False

    return True


class QuoHttpHandler:
    """
    HTTP Requests Handler for Quotient.
    """

    def __init__(self, bot):
        self.bot = bot

    async def handle(self):
        @routes.get("/")
        async def index(request):
            return web.json_response({"message": "Hello, world!"})

        @routes.get("/guild/settings")
        async def update_guild_settings(request: web.Request):
            _bool = validator(request)
            if not _bool:
                return web.json_response({"message": "Invalid token."}, status=401)

            res = await request.json()
            try:
                g_id = res["guild_id"]
            except KeyError:
                return web.Response(status=400)

            status = await update_guild_cache(self.bot, g_id)
            return web.json_response(status)

        @routes.get("/send/idp")
        async def send_idpass(request: web.Request):
            _bool = validator(request)
            if not _bool:
                return web.json_response({"message": "Invalid token."}, status=401)

            res = await request.json()
            status = await send_idp(self.bot, res.get("data"))
            return web.json_response(status)

        @routes.post("/scrim")
        async def create_scrim(request: web.Request):
            _bool = validator(request)
            if not _bool:
                return web.json_response({"message": "Invalid token."}, status=401)

            res = await request.json()

            res = await create_new_scrim(self.bot, res.get("data"))
            return web.json_response(res)

        @routes.patch("/scrim")
        async def edit_scrim(request: web.Request):
            _bool = validator(request)
            if not _bool:
                return web.json_response({"message": "Invalid token."}, status=401)

            res = await request.json()

            res = await edit_a_scrim(self.bot, res.get("data"))
            return web.json_response(res)

        @routes.delete("/scrim")
        async def delete_scrim(request: web.Request):
            _bool = validator(request)
            if not _bool:
                return web.json_response({"message": "Invalid token."}, status=401)

            res = await request.json()

            res = await delete_a_scrim(res.get("id"))
            return web.json_response(res)

        @routes.get("/partners")
        async def get_partners(request: web.Request):

            _bool = validator(request)
            if not _bool:
                return web.json_response({"message": "Invalid token."}, status=401)

            n = request.query.get("n", default=0)
            try:
                n = int(n)
            except ValueError:
                return web.Response(status=400)

            partners = await get_quo_partners(self.bot, n)

            return web.json_response(partners)

        app = web.Application()
        app.add_routes(routes)

        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, "0.0.0.0", config.IPC_PORT)
        await self.bot.wait_until_ready()
        await self.site.start()
