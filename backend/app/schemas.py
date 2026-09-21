from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class TelemetryFrame(BaseModel):
    timestamp: float
    armed: bool
    flight_mode: str
    altitude: float
    ground_speed: float
    battery_voltage: float
    pitch: float
    roll: float
    yaw: float
    packets_rx: int = 0
    packet_loss_pct: float = 0.0
    lat: float = 0.0
    lon: float = 0.0

class VehicleCommand(BaseModel):
    command: str  # ARM, DISARM, TAKEOFF, RTL, START_MISSION
    param1: Optional[float] = 0.0
    param2: Optional[float] = 0.0

class HandFrame(BaseModel):
    palm_position: List[float]  # [x, y, z]
    palm_velocity: List[float]
    grab_strength: float
    pinch_strength: float
    extended_fingers: int

from typing import Optional
from pydantic import BaseModel

class CommandRequest(BaseModel):
    command: str
    mode: Optional[str] = None