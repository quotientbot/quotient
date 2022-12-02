from fastapi import FastAPI

fastapi_app = FastAPI()


@fastapi_app.get("/")
async def root():
    return {"ping": "pong"}


from .payment import router as payment_router

fastapi_app.include_router(payment_router)
