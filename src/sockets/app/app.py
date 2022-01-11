from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from core import Quotient

import socketio


class QuoSocket(socketio.AsyncClient):
    bot: Quotient

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def emit(self, event, data=None, namespace=None, callback=None):
        event = f"response__{event}"
        return await super().emit(event, data=data, namespace=namespace, callback=callback)

    @staticmethod
    def int_parse(data: dict):
        for x, y in data.items():
            if isinstance(y, str) and y.isdigit():
                data[x] = int(y)

        return data


sio = QuoSocket(logger=True, engineio_logger=True)


@sio.on("*")
async def catch_all(event, data):
    print(event, data)
    data = QuoSocket.int_parse(data)
    print(f"{event} {data}")
    sio.bot.dispatch(event, data)
