from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import vehicle, telemetry, ws
from app.vehicle import vehicle_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(vehicle_manager.connect())
    yield

app = FastAPI(title="GCS Flight Core", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicle.router)
app.include_router(telemetry.router)
app.include_router(ws.router)

@app.get("/health")
async def health():
    return {"status": "healthy"}
