from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.vehicle import vehicle_manager
from app.gestures import classifier
from app.schemas import HandFrame
import asyncio
import json

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(vehicle_manager.latest_telemetry.model_dump_json())
            await asyncio.sleep(0.05)  # 20 Hz
    except WebSocketDisconnect:
        pass

@router.websocket("/ws/gestures")
async def gesture_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame = HandFrame(**json.loads(data))
            cmd = classifier.process_frame(frame)
            if cmd:
                await vehicle_manager.send_command(cmd)
                await websocket.send_json({"event": "command_triggered", "command": cmd})
    except WebSocketDisconnect:
        pass
