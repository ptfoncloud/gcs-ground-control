from pydantic import BaseModel

class Settings(BaseModel):
    MAVLINK_CONNECTION: str = "udpin:0.0.0.0:14550"
    DATABASE_URL: str = "sqlite+aiosqlite:///./telemetry.db"
    WS_HEARTBEAT_HZ: float = 20.0
    GESTURE_COOLDOWN_SEC: float = 1.5

settings = Settings()
