from socketio import AsyncClient

from .app import sio


async def init_application() -> AsyncClient:
    await sio.connect("")
    return sio
