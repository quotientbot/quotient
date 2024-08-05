from fastapi import FastAPI

from quotient.server import ws
from quotient.server.routers import youtube

fastapi_app = FastAPI()

fastapi_app.include_router(ws.router, tags=["ws"])
fastapi_app.include_router(youtube.router, prefix="/yt", tags=["youtube"])
