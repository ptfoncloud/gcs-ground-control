from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import TelemetryLog

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.get("/history")
async def get_telemetry_history(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TelemetryLog).order_by(TelemetryLog.id.desc()).limit(limit))
    return result.scalars().all()
