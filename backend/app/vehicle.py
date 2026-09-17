import asyncio
from pymavlink import mavutil
from app.config import settings
from app.schemas import TelemetryFrame

class VehicleManager:
    def __init__(self):
        self.master = None
        self.latest_telemetry = TelemetryFrame(
            timestamp=0.0, armed=False, flight_mode="UNKNOWN",
            altitude=0.0, ground_speed=0.0, battery_voltage=0.0,
            pitch=0.0, roll=0.0, yaw=0.0
        )
        self.running = False

    async def connect(self):
        # Wraps pymavlink non-blocking listen loop
        pass

    async def send_command(self, command: str, *args):
        pass

vehicle_manager = VehicleManager()
