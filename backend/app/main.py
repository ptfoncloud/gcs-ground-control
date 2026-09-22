import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import TelemetryFrame
from app.vehicle import vehicle_manager
from app.routers import commands, ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


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

# Command uplink (POST /api/command) and WebSocket downlink
# (/ws/telemetry, /ws/gestures) both live in their router modules —
# mounting them here is what actually makes those paths reachable.
app.include_router(commands.router)
app.include_router(ws.router)


# 1. Health Probe
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 2. REST Telemetry Snapshot
@app.get("/telemetry", response_model=TelemetryFrame)
@app.get("/api/telemetry", response_model=TelemetryFrame)
def get_telemetry():
    return vehicle_manager.latest_telemetry


# 3. Blackbox Telemetry Recorder Endpoints
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
