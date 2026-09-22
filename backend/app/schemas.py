from typing import List, Literal, Optional
from pydantic import BaseModel


class TelemetryFrame(BaseModel):
    timestamp: float = 0.0
    armed: bool = False
    flight_mode: str = "MANUAL"
    altitude: float = 0.0
    ground_speed: float = 0.0
    battery_voltage: float = 12.6
    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0
    packets_rx: int = 0
    packet_loss_pct: float = 0.0
    lat: float = 35.0594
    lon: float = -118.1517


class HandFrame(BaseModel):
    palm_position: List[float]  # [x, y, z]
    palm_velocity: List[float]
    grab_strength: float
    pinch_strength: float
    extended_fingers: int


# Keep in sync with ControlPanel.vue's `availableModes`.
FlightMode = Literal["GUIDED", "AUTO", "RTL", "LOITER", "STABILIZE"]


class CommandRequest(BaseModel):
    command: Literal["ARM", "DISARM", "SET_MODE"]
    mode: Optional[FlightMode] = None
    force: bool = False
