from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class WsConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_text("Hello, bro!")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def listen_to_websocket(self, websocket: WebSocket):
        try:
            while True:
                data = await websocket.receive_text()
                # Process the message as needed
        except WebSocketDisconnect as e:
            self.disconnect(websocket)
            print(f"WebSocket disconnected: {e.code} - {e.reason}")
        except Exception as e:
            self.disconnect(websocket)
            print(f"WebSocket error: {e}")


WS_CONNECTION_MANAGER = WsConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await WS_CONNECTION_MANAGER.connect(websocket)
    await WS_CONNECTION_MANAGER.listen_to_websocket(websocket)
