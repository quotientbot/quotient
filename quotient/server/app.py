from fastapi import FastAPI
from server.routers import payments, youtube

fastapi_app = FastAPI()
fastapi_app.include_router(youtube.router, prefix="/yt", tags=["youtube"])
