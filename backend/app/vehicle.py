import asyncio
import math
import time
from pymavlink import mavutil
from app.config import settings
from app.schemas import TelemetryFrame

class VehicleManager:
    def __init__(self):
        self.master = None
        self.latest_telemetry = TelemetryFrame(
            timestamp=0.0,
            armed=False,
            flight_mode="UNKNOWN",
            altitude=0.0,
            ground_speed=0.0,
            battery_voltage=0.0,
            pitch=0.0,
            roll=0.0,
            yaw=0.0,
            packets_rx=0,
            packet_loss_pct=0.0
        )
        # Link health & sequence loss tracking
        self.last_seq = None
        self.total_packets_received = 0
        self.total_packets_dropped = 0
        self.packet_loss_pct = 0.0
        self.running = False

    async def connect(self):
        conn_str = getattr(settings, "MAVLINK_CONNECTION_STRING", "udpin:127.0.0.1:14550")
        self.master = mavutil.mavlink_connection(conn_str)
        self.running = True
        print(f"[VEHICLE] Ingesting MAVLink on {conn_str}...")

        while self.running:
            try:
                # Non-blocking socket read
                msg = self.master.recv_match(blocking=False)
                if msg:
                    # 1. Packet Sequence & Loss Tracking (8-bit modulo 256)
                    current_seq = msg.get_seq()
                    if self.last_seq is not None:
                        # Accounts for 255 -> 0 overflow
                        dropped = (current_seq - self.last_seq - 1) % 256
                        if dropped > 0:
                            self.total_packets_dropped += dropped

                    self.last_seq = current_seq
                    self.total_packets_received += 1

                    total_expected = self.total_packets_received + self.total_packets_dropped
                    if total_expected > 0:
                        self.packet_loss_pct = round((self.total_packets_dropped / total_expected) * 100.0, 2)

                    # Update link stats on telemetry frame
                    self.latest_telemetry.packets_rx = self.total_packets_received
                    self.latest_telemetry.packet_loss_pct = self.packet_loss_pct

                    
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
                        self.latest_telemetry.altitude = round(msg.relative_alt / 1000.0, 2)
                        speed_ms = math.sqrt(msg.vx**2 + msg.vy**2) / 100.0
                        self.latest_telemetry.ground_speed = round(speed_ms, 2)
                        # MAVLink stores lat/lon as integers multiplied by 1e7
                        self.latest_telemetry.lat = round(msg.lat / 1e7, 7)
                        self.latest_telemetry.lon = round(msg.lon / 1e7, 7)

                    elif msg_type == "SYS_STATUS":
                        self.latest_telemetry.battery_voltage = round(msg.voltage_battery / 1000.0, 2)

                    self.latest_telemetry.timestamp = round(time.time(), 2)

            except Exception as e:
                print(f"[VEHICLE INGEST ERROR] {e}")

            # Non-blocking yield to event loop
            await asyncio.sleep(0.005)

    async def send_command(self, command: str, **kwargs) -> bool:
        if not self.master:
            print("[COMMAND ERROR] No master MAVLink connection initialized.")
            return False

        if not getattr(self.master, "destination_addr", None):
            print("[COMMAND ERROR] No remote target address discovered yet.")
            return False

        target_sys = self.master.target_system or 1
        target_comp = self.master.target_component or 1
        command = command.upper()

        try:
            if command in ["ARM", "DISARM"]:
                arm_val = 1.0 if command == "ARM" else 0.0
                self.master.mav.command_long_send(
                    target_sys,
                    target_comp,
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    0,          # Confirmation
                    arm_val,    # 1.0 to ARM, 0.0 to DISARM
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                )
                print(f"[COMMAND UPLINK] Dispatched {command} -> System {target_sys}")
                return True

            elif command == "SET_MODE":
                mode = kwargs.get("mode", "GUIDED").upper()
                mode_id = 4 if mode == "GUIDED" else self.master.mode_mapping().get(mode)
                if mode_id is None:
                    print(f"[COMMAND ERROR] Unknown flight mode: {mode}")
                    return False

                self.master.mav.set_mode_send(
                    target_sys,
                    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    mode_id
                )
                print(f"[COMMAND UPLINK] Mode set -> {mode} (ID {mode_id})")
                return True

            else:
                print(f"[COMMAND ERROR] Unsupported command: {command}")
                return False

        except Exception as e:
            print(f"[COMMAND EXEC EXCEPTION] Failed to dispatch {command}: {e}")
            return False

vehicle_manager = VehicleManager()