import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.vehicle import vehicle_manager
from app.routers import commands, telemetry, ws

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Launch MAVLink background ingest loop
    task = asyncio.create_task(vehicle_manager.connect())
    yield
    # Graceful shutdown
    vehicle_manager.running = False
    task.cancel()

app = FastAPI(title="GCS Mission Backend", lifespan=lifespan)

# Allow Vue dev server to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(commands.router)
app.include_router(telemetry.router)
app.include_router(ws.router)

@app.get("/")
def root():
    return {"status": "ONLINE", "system": "GCS Mission Core"}
