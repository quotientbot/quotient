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
        return await super().emit("response__" + event, data=data, namespace=namespace, callback=callback)

    @staticmethod
    def int_parse(data):
        if not isinstance(data, dict):
            return data

        for x, y in data.items():
            if isinstance(y, str) and y.isdigit():
                data[x] = int(y)

        return data


sio = QuoSocket(logger=True, engineio_logger=True)
ignored = ("update_total_votes", "update_votes_leaderboard")


@sio.on("*")
async def catch_all(event, data):
    if event in ignored:
        return

    data = QuoSocket.int_parse(data)

    r, e, u = event.split("__")
    data["user__id"] = u
    sio.bot.dispatch(r + "__" + e, u, data)
