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
            flight_mode="MANUAL",
            altitude=0.0,
            ground_speed=0.0,
            battery_voltage=12.6,
            pitch=0.0,
            roll=0.0,
            yaw=0.0,
            packets_rx=0,
            packet_loss_pct=0.0,
            lat=35.0594,
            lon=-118.1517,
        )
        # Link health & sequence loss tracking
        self.last_seq = None
        self.packets_rx = 0
        self.packets_lost = 0
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
                        if 0 < dropped < 50:
                            self.packets_lost += dropped

                    self.last_seq = current_seq
                    self.packets_rx += 1

                    total_expected = self.packets_rx + self.packets_lost
                    if total_expected > 0:
                        self.packet_loss_pct = round(
                            (self.packets_lost / total_expected) * 100.0, 2
                        )

                    # Update link stats on telemetry frame
                    self.latest_telemetry.packets_rx = self.packets_rx
                    self.latest_telemetry.packet_loss_pct = self.packet_loss_pct

                    msg_type = msg.get_type()

                    if msg_type == "HEARTBEAT":
                        is_armed = bool(
                            msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
                        )
                        mode_name = (
                            "GUIDED"
                            if msg.custom_mode == 4
                            else f"MODE_{msg.custom_mode}"
                        )
                        self.latest_telemetry.armed = is_armed
                        self.latest_telemetry.flight_mode = mode_name

                    elif msg_type == "ATTITUDE":
                        self.latest_telemetry.roll = round(msg.roll, 3)
                        self.latest_telemetry.pitch = round(msg.pitch, 3)
                        self.latest_telemetry.yaw = round(msg.yaw, 3)

                    elif msg_type == "GLOBAL_POSITION_INT":
                        self.latest_telemetry.altitude = round(
                            msg.relative_alt / 1000.0, 2
                        )
                        speed_ms = math.sqrt(msg.vx**2 + msg.vy**2) / 100.0
                        self.latest_telemetry.ground_speed = round(speed_ms, 2)
                        # MAVLink stores lat/lon as integers multiplied by 1e7
                        self.latest_telemetry.lat = round(msg.lat / 1e7, 7)
                        self.latest_telemetry.lon = round(msg.lon / 1e7, 7)

                    elif msg_type == "SYS_STATUS":
                        self.latest_telemetry.battery_voltage = round(
                            msg.voltage_battery / 1000.0, 2
                        )

                    self.latest_telemetry.timestamp = round(time.time(), 2)

            except Exception as e:
                print(f"[VEHICLE INGEST ERROR] {e}")

            # Non-blocking yield to event loop
            await asyncio.sleep(0.005)

    def send_arm_command(self, arm: bool, force: bool = False) -> bool:
        """Dispatches MAV_CMD_COMPONENT_ARM_DISARM over MAVLink."""
        if not self.master:
            print("[COMMAND ERROR] No master MAVLink connection initialized.")
            return False

        try:
            target_sys = getattr(self.master, "target_system", None) or 1
            target_comp = getattr(self.master, "target_component", None) or 1
            param1 = 1.0 if arm else 0.0
            param2 = 21196.0 if force else 0.0

            self.master.mav.command_long_send(
                target_sys,
                target_comp,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,
                param1,
                param2,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            )
            print(f"[COMMAND UPLINK] Dispatched ARM={arm} (force={force}) -> Sys {target_sys}")
            return True
        except Exception as e:
            print(f"[COMMAND EXEC EXCEPTION] Arm failure: {e}")
            return False

    def set_mode(self, mode_name: str) -> bool:
        """Dispatches flight mode change over MAVLink."""
        if not self.master:
            print("[COMMAND ERROR] No master MAVLink connection initialized.")
            return False

        try:
            mode_upper = mode_name.upper()
            target_sys = getattr(self.master, "target_system", None) or 1

            if hasattr(self.master, "mode_mapping"):
                mode_map = self.master.mode_mapping()
                if mode_map and mode_upper in mode_map:
                    self.master.set_mode(mode_map[mode_upper])
                    return True

            mode_id = 4 if mode_upper == "GUIDED" else 0
            self.master.mav.set_mode_send(
                target_sys,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id,
            )
            print(f"[COMMAND UPLINK] Mode set -> {mode_name}")
            return True
        except Exception as e:
            print(f"[COMMAND EXEC EXCEPTION] Mode failure: {e}")
            return False

    async def send_command(self, command: str, **kwargs) -> bool:
        """General command router."""
        command = command.upper()
        if command in ["ARM", "DISARM"]:
            return self.send_arm_command(arm=(command == "ARM"), force=kwargs.get("force", False))
        elif command == "SET_MODE":
            return self.set_mode(kwargs.get("mode", "GUIDED"))
        return False


vehicle_manager = VehicleManager()