import socketio

sio = socketio.AsyncClient(logger=True, engineio_logger=True)


@sio.event()
async def connect():
    print("connection established")
