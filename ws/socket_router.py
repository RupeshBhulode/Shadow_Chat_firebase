from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.manager import manager  # ✅ Use the singleton instance
from routers.message_router import store_encrypted_message  # ✅ Import the shared logic

socket_router = APIRouter()

@socket_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            sender = data["sender"]
            receiver = data["receiver"]
            message = data["message"]

            # ✅ Optional: Basic validation
            if sender != user_id:
                await websocket.send_text("Sender ID mismatch. You are not authorized.")
                continue

            # ✅ Store in DB and send real-time
            await store_encrypted_message(sender, receiver, message)

    except WebSocketDisconnect:
        manager.disconnect(user_id)

