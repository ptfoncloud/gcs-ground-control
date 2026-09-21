import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.schemas import TelemetryFrame
from app.vehicle import vehicle_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the MAVLink ingestion loop on server startup
    ingest_task = asyncio.create_task(vehicle_manager.connect())
    yield
    # Clean shutdown
    vehicle_manager.running = False
    ingest_task.cancel()


app = FastAPI(
    title="Aerospace Ground Control Station Core",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ArmRequest(BaseModel):
    force: bool = False


class FlightModeRequest(BaseModel):
    mode: str


# 1. Health Probe
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 2. REST Telemetry Snapshot
@app.get("/telemetry", response_model=TelemetryFrame)
@app.get("/api/telemetry", response_model=TelemetryFrame)
def get_telemetry():
    return vehicle_manager.latest_telemetry


# 3. Command Uplink Endpoints
@app.post("/command/arm")
@app.post("/api/command/arm")
def arm_vehicle(cmd: ArmRequest):
    vehicle_manager.send_arm_command(arm=True, force=cmd.force)
    return {"status": "DISPATCHED", "command": "ARM", "force": cmd.force}


@app.post("/command/disarm")
@app.post("/api/command/disarm")
def disarm_vehicle(cmd: ArmRequest):
    vehicle_manager.send_arm_command(arm=False, force=cmd.force)
    return {"status": "DISPATCHED", "command": "DISARM", "force": cmd.force}


@app.post("/command/mode")
@app.post("/api/command/mode")
def set_flight_mode(cmd: FlightModeRequest):
    vehicle_manager.set_mode(cmd.mode)
    return {"status": "DISPATCHED", "target_mode": cmd.mode}


# 4. Blackbox Telemetry Recorder Endpoints
@app.post("/record/start")
@app.post("/api/record/start")
def start_recording():
    vehicle_manager.start_recording()
    return {"status": "RECORDING_STARTED"}


@app.post("/record/stop")
@app.post("/api/record/stop")
def stop_recording():
    vehicle_manager.stop_recording()
    return {
        "status": "RECORDING_STOPPED",
        "frames_captured": len(vehicle_manager.recorded_frames),
    }


@app.get("/record/status")
@app.get("/api/record/status")
def recording_status():
    return {
        "is_recording": vehicle_manager.is_recording,
        "frames_captured": len(vehicle_manager.recorded_frames),
    }


@app.get("/record/export")
@app.get("/api/record/export")
def export_recording():
    csv_data = vehicle_manager.get_csv_export()
    if not csv_data:
        return Response(content="No telemetry recorded.", status_code=400, media_type="text/plain")

    timestamp_int = int(vehicle_manager.latest_telemetry.timestamp) if vehicle_manager.latest_telemetry.timestamp else 0
    filename = f"flight_log_{timestamp_int}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# 5. High-frequency WebSocket Downlink
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(
                vehicle_manager.latest_telemetry.model_dump_json()
            )
            await asyncio.sleep(0.05)  # 20 Hz
    except WebSocketDisconnect:
        pass