import asyncio
import csv
import json
import math
import os
import sys
from datetime import datetime

# URL of the running FastAPI telemetry websocket. Override with
# GCS_WS_URL if the backend isn't on this same machine.
WS_URL = os.environ.get("GCS_WS_URL", "ws://127.0.0.1:8080/ws/telemetry")
LOGS_DIR = "flight_logs"

CSV_HEADERS = [
    "timestamp",
    "armed",
    "flight_mode",
    "altitude_m",
    "ground_speed_ms",
    "battery_voltage_v",
    "pitch_deg",
    "roll_deg",
    "yaw_deg",
    "lat",
    "lon",
    "packets_rx",
    "packet_loss_pct",
]

async def record():
    try:
        import websockets
    except ImportError:
        print("[ERROR] 'websockets' library not found. Run: pip install websockets")
        return

    os.makedirs(LOGS_DIR, exist_ok=True)
    filename = f"{LOGS_DIR}/flight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    print("=======================================================")
    print(f"  GCS BLACKBOX FLIGHT RECORDER")
    print(f"  Streaming from: {WS_URL}")
    print(f"  Writing to:     {filename}")
    print("  Press Ctrl+C at any time to stop recording.")
    print("=======================================================\n")

    frame_count = 0

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)

        try:
            async with websockets.connect(WS_URL) as ws:
                while True:
                    raw_msg = await ws.recv()
                    data = json.loads(raw_msg)

                    # The websocket payload's pitch/roll/yaw are radians,
                    # straight off the MAVLink ATTITUDE message — convert
                    # here so the pitch_deg/roll_deg/yaw_deg headers above
                    # are actually true.
                    writer.writerow([
                        data.get("timestamp", 0.0),
                        1 if data.get("armed") else 0,
                        data.get("flight_mode", "UNKNOWN"),
                        data.get("altitude", 0.0),
                        data.get("ground_speed", 0.0),
                        data.get("battery_voltage", 0.0),
                        math.degrees(data.get("pitch", 0.0)),
                        math.degrees(data.get("roll", 0.0)),
                        math.degrees(data.get("yaw", 0.0)),
                        data.get("lat", 0.0),
                        data.get("lon", 0.0),
                        data.get("packets_rx", 0),
                        data.get("packet_loss_pct", 0.0),
                    ])
                    frame_count += 1

                    # Live terminal counter
                    sys.stdout.write(
                        f"\r[REC] Captured: {frame_count:05d} frames | "
                        f"ALT: {data.get('altitude', 0.0):5.1f}m | "
                        f"MODE: {data.get('flight_mode', 'N/A'):<7}"
                    )
                    sys.stdout.flush()

        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        except ConnectionRefusedError:
            print(f"\n[ERROR] Could not connect to {WS_URL}. Is Uvicorn running on port 8080?")
            return

    print(f"\n\n[COMPLETE] Recording saved successfully: {filename} ({frame_count} rows)")

if __name__ == "__main__":
    try:
        asyncio.run(record())
    except KeyboardInterrupt:
        pass