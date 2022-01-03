import socketio

from bot import bot

sio = socketio.AsyncClient()


@sio.event()
async def connect():
    print("connection established")
