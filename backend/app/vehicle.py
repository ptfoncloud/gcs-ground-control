import asyncio
import logging
import math
import time
from pymavlink import mavutil
from app.config import settings
from app.schemas import TelemetryFrame

logger = logging.getLogger(__name__)

# Modes offered in the console (ControlPanel.vue's <select>) and
# will accept over the API. Anything else is rejected rather than silently
# dispatched as mode 0.
FALLBACK_MODE_IDS = {
    "STABILIZE": 0,
    "GUIDED": 4,
    "AUTO": 3,
    "LOITER": 5,
    "RTL": 6,
}


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

        # Blackbox flight recorder. Initialized once here — NOT inside the
        # ingest loop, which used to reset both of these on every single
        # received MAVLink message (i.e. recording never actually
        # accumulated more than one frame).
        self.is_recording = False
        self.recorded_frames = []

    async def connect(self):
        conn_str = settings.MAVLINK_CONNECTION_STRING
        self.master = mavutil.mavlink_connection(conn_str)
        self.running = True
        logger.info("Ingesting MAVLink on %s...", conn_str)

        while self.running:
            try:
                # Non-blocking socket read
                msg = self.master.recv_match(blocking=False)
                if msg:
                    self._track_sequence(msg.get_seq())
                    self.latest_telemetry.packets_rx = self.packets_rx
                    self.latest_telemetry.packet_loss_pct = self.packet_loss_pct

                    self._handle_message(msg)

                    self.latest_telemetry.timestamp = round(time.time(), 2)
                    if self.is_recording:
                        self.recorded_frames.append(self.latest_telemetry.model_dump())

            except Exception:
                logger.exception("Vehicle ingest error")

            # Non-blocking yield to event loop
            await asyncio.sleep(0.005)

    def _track_sequence(self, current_seq: int) -> None:
        """
        Updates packet receive/loss counters from the 8-bit modulo-256
        MAVLink sequence number.

        A packet is only treated as forward progress (and only then does
        `last_seq` advance) when its delta from the last-seen sequence is
        in [0, 50). Anything else; an exact duplicate, or a stale/
        reordered packet arriving behind our current baseline — is
        ignored for loss-counting purposes AND deliberately does not
        rewind `last_seq`, so a late/reordered packet can't corrupt the
        loss calculation for every packet that arrives after it.
        """
        if self.last_seq is not None:
            delta = (current_seq - self.last_seq - 1) % 256
            if 0 <= delta < 50:
                self.packets_lost += delta
                self.last_seq = current_seq
            # else: duplicate or out-of-order/stale packet — don't count
            # as loss, don't advance last_seq.
        else:
            self.last_seq = current_seq

        self.packets_rx += 1
        total_expected = self.packets_rx + self.packets_lost
        if total_expected > 0:
            self.packet_loss_pct = round(
                (self.packets_lost / total_expected) * 100.0, 2
            )

    def _handle_message(self, msg) -> None:
        """Dispatches a decoded MAVLink message to its field-update handler."""
        msg_type = msg.get_type()
        if msg_type == "HEARTBEAT":
            self._handle_heartbeat(msg)
        elif msg_type == "ATTITUDE":
            self._handle_attitude(msg)
        elif msg_type == "GLOBAL_POSITION_INT":
            self._handle_global_position(msg)
        elif msg_type == "SYS_STATUS":
            self._handle_sys_status(msg)

    def _handle_heartbeat(self, msg) -> None:
        is_armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        mode_name = (
            "GUIDED" if msg.custom_mode == 4 else f"MODE_{msg.custom_mode}"
        )
        self.latest_telemetry.armed = is_armed
        self.latest_telemetry.flight_mode = mode_name

    def _handle_attitude(self, msg) -> None:
        self.latest_telemetry.roll = round(msg.roll, 3)
        self.latest_telemetry.pitch = round(msg.pitch, 3)
        self.latest_telemetry.yaw = round(msg.yaw, 3)

    def _handle_global_position(self, msg) -> None:
        self.latest_telemetry.altitude = round(msg.relative_alt / 1000.0, 2)
        speed_ms = math.sqrt(msg.vx**2 + msg.vy**2) / 100.0
        self.latest_telemetry.ground_speed = round(speed_ms, 2)
        self.latest_telemetry.lat = round(msg.lat / 1e7, 7)
        self.latest_telemetry.lon = round(msg.lon / 1e7, 7)

    def _handle_sys_status(self, msg) -> None:
        self.latest_telemetry.battery_voltage = round(msg.voltage_battery / 1000.0, 2)

    def send_arm_command(self, arm: bool, force: bool = False) -> bool:
        """Dispatches MAV_CMD_COMPONENT_ARM_DISARM over MAVLink."""
        if not self.master:
            logger.error("No master MAVLink connection initialized.")
            return False

        try:
            target_sys = getattr(self.master, "target_system", None) or 1
            target_comp = getattr(self.master, "target_component", None) or 1
            param1 = 1.0 if arm else 0.0
            param2 = 21196.0 if force else 0.0  # MAVLink force-arm/disarm magic number

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
            logger.info(
                "Dispatched ARM=%s (force=%s) -> Sys %s", arm, force, target_sys
            )
            return True
        except Exception:
            logger.exception("Arm command dispatch failed")
            return False

    def set_mode(self, mode_name: str) -> bool:
        """
        Dispatches a flight mode change over MAVLink.

        Raises ValueError for a mode we don't recognize, rather than
        silently dispatching mode 0 (STABILIZE on most ArduPilot builds).
        """
        if not self.master:
            logger.error("No master MAVLink connection initialized.")
            return False

        mode_upper = mode_name.upper()
        target_sys = getattr(self.master, "target_system", None) or 1

        try:
            if hasattr(self.master, "mode_mapping"):
                mode_map = self.master.mode_mapping()
                if mode_map and mode_upper in mode_map:
                    self.master.set_mode(mode_map[mode_upper])
                    logger.info("Mode set -> %s (via mode_mapping)", mode_name)
                    return True

            if mode_upper not in FALLBACK_MODE_IDS:
                raise ValueError(f"Unsupported flight mode '{mode_name}'")

            self.master.mav.set_mode_send(
                target_sys,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                FALLBACK_MODE_IDS[mode_upper],
            )
            logger.info("Mode set -> %s (fallback map)", mode_name)
            return True
        except ValueError:
            raise
        except Exception:
            logger.exception("Mode change dispatch failed")
            return False

    async def send_command(self, command: str, **kwargs) -> bool:
        """General command router. Raises ValueError for an unknown command."""
        command = command.upper()
        if command in ("ARM", "DISARM"):
            return self.send_arm_command(
                arm=(command == "ARM"), force=kwargs.get("force", False)
            )
        elif command == "SET_MODE":
            return self.set_mode(kwargs.get("mode") or "GUIDED")
        raise ValueError(f"Unsupported command '{command}'")

    def start_recording(self):
        self.recorded_frames.clear()
        self.is_recording = True
        logger.info("Blackbox recording started.")

    def stop_recording(self):
        self.is_recording = False
        logger.info("Blackbox recording stopped. Total frames: %d", len(self.recorded_frames))

    def get_csv_export(self) -> str:
        import io
        import csv

        if not self.recorded_frames:
            return ""

        output = io.StringIO()
        fieldnames = list(self.recorded_frames[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(self.recorded_frames)
        return output.getvalue()


vehicle_manager = VehicleManager()
