from fastapi import FastAPI

from quotient.server import ws
from quotient.server.routers import payments

fastapi_app = FastAPI()

fastapi_app.include_router(ws.router, tags=["ws"])
fastapi_app.include_router(payments.router, tags=["payments"])
