import asyncio
import math
import time
from pymavlink import mavutil
from app.config import settings
from app.schemas import TelemetryFrame

  # update as of 11:14PM 9/16/26 i unfortunately forgot to write this 
  # and then wondered why it wasnt working, problem is solved ;)

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
        # Target local loopback UDP port 14550
        conn_str = getattr(settings, "MAVLINK_CONNECTION_STRING", "udpin:127.0.0.1:14550")
        self.master = mavutil.mavlink_connection(conn_str)
        self.running = True
        print(f"[VEHICLE] Ingesting MAVLink on {conn_str}...")

        while self.running:
            try:
                # Non-blocking poll of the UDP socket buffer
                msg = self.master.recv_match(blocking=False)
                if msg:
                    msg_type = msg.get_type()

                    if msg_type == "HEARTBEAT":
                        is_armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                        mode_name = "GUIDED" if msg.custom_mode == 4 else f"MODE_{msg.custom_mode}"
                        self.latest_telemetry.armed = is_armed
                        self.latest_telemetry.flight_mode = mode_name

                    elif msg_type == "ATTITUDE":
                        self.latest_telemetry.roll = round(msg.roll, 3)
                        self.latest_telemetry.pitch = round(msg.pitch, 3)
                        self.latest_telemetry.yaw = round(msg.yaw, 3)

                    elif msg_type == "GLOBAL_POSITION_INT":
                        # Convert mm to meters
                        self.latest_telemetry.altitude = round(msg.relative_alt / 1000.0, 2)
                        # Groundspeed magnitude from vx/vy (cm/s -> m/s)
                        speed_ms = math.sqrt(msg.vx**2 + msg.vy**2) / 100.0
                        self.latest_telemetry.ground_speed = round(speed_ms, 2)

                    elif msg_type == "SYS_STATUS":
                        # Convert mV to Volts
                        self.latest_telemetry.battery_voltage = round(msg.voltage_battery / 1000.0, 2)

                    self.latest_telemetry.timestamp = round(time.time(), 2)

            except Exception as e:
                print(f"[VEHICLE INGEST ERROR] {e}")

            # Yield control so FastAPI can actually service the WebSocket loop
            await asyncio.sleep(0.005)

    async def send_command(self, command: str, *args):
        pass

vehicle_manager = VehicleManager()
