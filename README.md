# Autonomous Flight Core: Ground Control Station & HIL Testbed - PROTOTYPE

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vuedotjs&logoColor=white)
![MAVLink](https://img.shields.io/badge/MAVLink-2.0-blue?style=flat)
![Tests](https://img.shields.io/badge/Tests-15%2F15%20Passing-success?style=flat)
![License](https://img.shields.io/badge/License-MIT-gray?style=flat)


<p align="center">
  <img src="assets/GCSMissionConsole-Opera2026-09-2117-42-15-ezgif.com-video-to-gif-converter.gif" alt="Mission Console Live Flight Demo" width="750">
</p>


A full-stack Ground Control Station and Hardware-in-the-Loop (HIL) testbed built with **FastAPI**, **Vue 3**, and **MAVLink v2**. 

It handles bidirectional vehicle operations: streaming telemetry down from an autopilot over UDP at 20 Hz, broadcasting it to a browser HUD via WebSockets, and uplinking commands (Arm/Disarm, Flight Modes) back to the vehicle with verified hardware acknowledgments.

---

## Architecture

Telemetry streaming and command uplinks are completely decoupled to prevent command latency or head-of-line blocking:

```mermaid
flowchart TD
    subgraph UI ["Mission HUD (Vue 3 / Vite :5173)"]
        HUD["ControlPanel.vue & Telemetry Gauges"]
        Store["Pinia Store (vehicleStore.js)"]
    end

    subgraph Server ["Core Gateway (FastAPI :8080)"]
        REST["REST API (/api/command)"]
        WS["WebSocket Hub (/ws/telemetry)"]
        Worker["VehicleManager (asyncio / pymavlink)"]
    end

    subgraph Autopilot ["SITL Flight Vehicle (:14550)"]
        SITL["mock_mavlink.py (20 Hz)"]
    end

    HUD -->|1. HTTP POST Payload| REST
    REST -->|2. Encode Frame| Worker
    Worker -->|3. UDP MAVLink COMMAND_LONG| SITL

    SITL -->|4. UDP MAVLink Telemetry 20Hz| Worker
    Worker -->|5. Push Ingested State| WS
    WS -->|6. JSON Frame Broadcast| Store
    Store --> HUD
```

* **Downlink (Telemetry @ 20 Hz):** The SITL feeder generates binary MAVLink datagrams over UDP port `14550`. FastAPI drains the socket non-blockingly, caches current flight state, and fans out JSON frames over WebSockets.
* **Uplink (Commanding):** HUD actions issue an HTTP `POST` to `/api/command`. The backend parses the payload into a typed MAVLink `COMMAND_LONG` or `SET_MODE` packet and transmits it over UDP to the vehicle.
* **Telemetry-Verified State:** The UI never flips state optimistically. The propulsion indicator only switches to **ARMED** once the autopilot returns a valid `COMMAND_ACK` and sets the `MAV_MODE_FLAG_SAFETY_ARMED` bit (`0x80`) in its outbound `HEARTBEAT` stream.

---

## Technical Edge Cases & Engineering Notes

### 1. UDP vs TCP for Flight Telemetry
Standard web services rely on TCP, but TCP introduces Head-of-Line (HoL) blocking. Over a lossy RF link, a dropped attitude packet at $t = 100\text{ ms}$ stalls the connection while the protocol waits for a retransmission—rendering data stale on arrival. Using UDP allows the ingest loop to discard dropped or late packets instantly, ensuring the HUD renders current flight data.

### 2. Windows Winsock Sockets
Running non-blocking UDP sockets under Windows required addressing two OS-level Winsock quirks:
* **`WinError 10022` (`WSAEINVAL`):** Calling `recvfrom()` on an unbound non-blocking UDP socket is valid on Linux (which assigns an ephemeral port automatically), but fails on Windows. Explicitly calling `mav.port.bind(('', 0))` fixes this.
* **`WinError 10054` (`WSAECONNRESET`):** If UDP packets are transmitted before the backend binds port 14550, Windows catches the ICMP "Port Unreachable" response and raises `ConnectionResetError` on the *next* read. The ingest loop wraps reads in non-blocking exception guards to swallow cold-start resets cleanly.

### 3. Defensive Frontend Lifecycles
All feedback timers are tied to component unmount hooks (`onUnmounted`). Triggering multiple commands in rapid succession clears any active timer before starting a new one, preventing race conditions from wiping newer status messages prematurely or leaking memory.

---

## Telemetry & Command Specifications

### Ingested MAVLink Frames

| Message | ID | Decoded Parameters | Ingest Rate |
| :--- | :--- | :--- | :--- |
| **`HEARTBEAT`** | `#0` | Arm status bitmask (`0x80`), Custom flight mode | 1 Hz |
| **`ATTITUDE`** | `#30` | Roll (rad), Pitch (rad), Yaw (rad) | 20 Hz |
| **`GLOBAL_POSITION_INT`** | `#33` | Relative Altitude AGL (mm), Ground speed (cm/s), Heading (cdeg) | 10 Hz |
| **`SYS_STATUS`** | `#1` | Battery voltage (mV), Remaining capacity (%) | 2 Hz |
| **`COMMAND_ACK`** | `#77` | Command confirmation ID, `MAV_RESULT_ACCEPTED` status | Event-driven |

### REST Uplink Schema

```http
POST /api/command HTTP/1.1
Content-Type: application/json

{
  "command": "ARM",
  "mode": null
}
```

```http
POST /api/command HTTP/1.1
Content-Type: application/json

{
  "command": "SET_MODE",
  "mode": "RTL"
}
```

---

## Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── config.py              # Env-driven runtime settings (pydantic-settings)
│   │   ├── main.py                # FastAPI app, health/telemetry/record REST + router mounts
│   │   ├── schemas.py             # Pydantic telemetry & command models
│   │   ├── vehicle.py             # UDP MAVLink ingestion loop & state tracking
│   │   ├── gestures.py            # Gesture classifier (stub — not implemented yet)
│   │   └── routers/
│   │       ├── commands.py        # POST /api/command — canonical command uplink
│   │       └── ws.py              # /ws/telemetry and /ws/gestures WebSocket endpoints
│   └── tests/
│       ├── conftest.py            # Pytest fixtures & async HTTP test client
│       ├── test_api.py            # API health check verification
│       ├── test_command_interlocks.py  # Safety state machine tests
│       └── test_mavlink_integrity.py   # Modulo-256 math & packet drop tests
├── scripts/
│   ├── mock_mavlink.py            # Kinematic flight sim & telemetry generator (repo root, not backend/)
│   └── record_telemetry.py        # Standalone CLI blackbox recorder (CSV, via the WS feed)
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ArtificialHorizon.vue # MIL-STD-1787C Primary Flight Display
    │   │   ├── ControlPanel.vue      # Command uplink buttons & safety interlocks
    │   │   ├── RecorderControls.vue  # Blackbox recorder start/stop/export
    │   │   ├── TacticalMap.vue       # Leaflet moving map with CartoDB dark tiles
    │   │   └── TelemetryCard.vue     # High-contrast instrumentation readouts
    │   ├── stores/
    │   │   └── vehicleStore.js       # Pinia reactive telemetry state
    │   ├── utils/
    │   │   └── audioCaution.js       # Native Web Audio API dual-tone synthesizer
    │   ├── config.js                  # Backend URL resolution (see below)
    │   ├── App.vue                   # Dual-deck cockpit interface
    │   └── main.js
    └── package.json

```

The backend no longer ships a database layer — an unwired SQLAlchemy/SQLite
subsystem (`database.py`, `models.py`, a `/telemetry/history` route) used to
exist here, but nothing ever wrote to it. Flight history is captured by the
blackbox recorder (`/api/record/*`, exported as CSV) instead.

---

## Quickstart

### Automated Launch (Recommended)
Clone the repository and run the PowerShell orchestrator:

```text
============================= test session starts ==============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.15.1, asyncio-1.4.0

tests/test_api.py::test_health PASSED                                     [  8%]
tests/test_command_interlocks.py::TestCommandInterlocks::test_arm_command_dispatch_does_not_optimistically_arm PASSED [ 16%]
tests/test_command_interlocks.py::TestCommandInterlocks::test_emergency_motor_cutoff_validates_payload PASSED [ 25%]
tests/test_command_interlocks.py::TestCommandInterlocks::test_telemetry_schema_snapshot PASSED                 [ 33%]
tests/test_command_interlocks.py::TestCommandInterlocks::test_authoritative_heartbeat_state_transition PASSED [ 41%]
tests/test_mavlink_integrity.py::TestMavlinkSequenceMath::test_nominal_continuous_stream PASSED                [ 50%]
tests/test_mavlink_integrity.py::TestMavlinkSequenceMath::test_single_packet_drop PASSED                      [ 58%]
tests/test_mavlink_integrity.py::TestMavlinkSequenceMath::test_multi_packet_burst_loss PASSED                  [ 66%]
tests/test_mavlink_integrity.py::TestMavlinkSequenceMath::test_uint8_rollover_nominal PASSED                  [ 75%]
tests/test_mavlink_integrity.py::TestMavlinkSequenceMath::test_uint8_rollover_with_loss PASSED                 [ 83%]
tests/test_mavlink_integrity.py::TestMavlinkSequenceMath::test_duplicate_frame_rejection PASSED               [ 91%]
tests/test_mavlink_integrity.py::TestVehicleManagerPacketIntegration::test_vehicle_manager_ingestion_updates_loss PASSED [100%]

============================== 12 passed in 0.06s ==============================

```

---

### Manual Launch

**1. Backend Gateway**
```powershell
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
python -m pytest tests/ -v
uvicorn app.main:app --host 0.0.0.0 --port 8080

```

### Step 2: Frontend Mission Console

```bash
cd frontend
npm install
npm run dev

```

Open `http://localhost:5173` in your browser. The console talks to the
backend at `http://<the-host-you-opened-this-page-from>:8080` by
default (see `frontend/src/config.js`) — so this also works unmodified
when you open it from another machine on the same network as the
backend (e.g. a laptop connecting to a companion computer on a real
vehicle). Set `VITE_API_BASE_URL` at build time (see `.env.example`)
only if the backend lives somewhere else entirely.

### Step 3: Flight Telemetry Simulator (HIL Stream)

`mock_mavlink.py` lives at the **repository root**, not under `backend/`.
In a separate terminal, with the backend virtual environment active:

```bash
# From the repository root:
python scripts/mock_mavlink.py

```

---

## Verification Sequence

1. Open `http://localhost:5173`. Confirm the top-right indicator shows **`LINK ACTIVE`** and the propulsion badge shows **`DISARMED`**.
2. Click **`ARM PROPULSION`**.
   * Status updates to `TRANSMITTING ARM...` and then locks into `UPLINK ACKNOWLEDGED: ARM`.
   * SITL terminal confirms: `[SITL RX] Propulsion Interlock -> ARMED`.
   * HUD badge turns red **`ARMED`**, and simulated vehicle climb and ground speed begin accelerating.
3. Select **`RTL`** from the mode selector and click **`SET MODE`**.
   * SITL terminal confirms: `[SITL RX] Mode Switched -> ID 6`.
   * HUD flight mode updates to **`RTL`**.
4. Click **`FORCE DISARM`**.
   * SITL terminal registers `[SITL RX] Propulsion Interlock -> DISARMED`.
   * Altitude and ground speed decay to zero.

---

## Roadmap

- [x] Bidirectional UDP MAVLink translation layer
- [x] Real-time WebSocket telemetry distribution
- [x] Interlocked propulsion state & flight mode uplinks
- [x] Windows Winsock socket hardening (`10022` / `10054`)
