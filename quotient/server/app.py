from fastapi import FastAPI

from quotient.server import ws

fastapi_app = FastAPI()

fastapi_app.include_router(ws.router, tags=["ws"])
