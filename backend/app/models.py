from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime, timezone
from app.database import Base

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    altitude = Column(Float)
    ground_speed = Column(Float)
    battery_voltage = Column(Float)
    flight_mode = Column(String)
    pitch = Column(Float)
    roll = Column(Float)
    yaw = Column(Float)
