
# Autonomous Flight Core: Ground Control Station & HIL Testbed

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=flat&logo=vuedotjs&logoColor=white)
![MAVLink](https://img.shields.io/badge/MAVLink-2.0-blue?style=flat)
![Tests](https://img.shields.io/badge/Tests-12%2F12%20Passing-success?style=flat)
![License](https://img.shields.io/badge/License-MIT-gray?style=flat)

An asynchronous, hardware-agnostic Ground Control Station (GCS) and Hardware-in-the-Loop (HIL) telemetry testbed built from first principles. Ingests native binary MAVLink 2.0 telemetry streams over UDP, computes transport-layer frame loss via 8-bit unsigned modular arithmetic, and renders low-latency telemetry to a cockpit interface compliant with MIL-STD-1787C human-factors specifications.

---

## 1. System Architecture

```text
========================================================================================
[VEHICLE / SITL / HARDWARE TESTBED]  ──(UDP:14550 MAVLink 2.0)──►  [FASTAPI TELEMETRY CORE]
                                                                            │
      ┌─────────────────────────────────────────────────────────────────────┴────────┐
      ▼ (20 Hz Non-Blocking Async WebSocket)                                         ▼ (REST /api)
[VUE 3 MISSION CONSOLE]                                                   [COMMAND DISPATCH]
 ├── MIL-STD-1787C Primary Flight Display (Pure SVG ADI)                   ├── Mode Transitions
 ├── Tactical Moving Map (Leaflet / CartoDB Dark Matter)                   └── Arm/Disarm Interlocks
 ├── Modulo-256 Packet Loss Watchdog Engine                                    (Strict Bitmask 0x80)
 └── Web Audio API Caution Synthesizer (750/900 Hz Dual Tone)
========================================================================================

```

---

## 2. Core Subsystems

### Transport & Ingestion Layer

* **Non-Blocking Ingestion:** Powered by Python's `asyncio` event loop and `pymavlink` bound to UDP port `14550`. Ingest operations are decoupled from HTTP serving threads to prevent Head-of-Line (HoL) blocking and gracefully absorb socket resets (`WSAECONNRESET` / `WinError 10054`).
* **High-Frequency WebSocket Fanout:** Pydantic-validated telemetry frames are broadcast to connected client consoles at a synchronized 20 Hz update rate.

### Protocol Integrity & Modulo-256 Loss Tracking

Packet drop rates are calculated at the transport boundary using MAVLink's 8-bit wire sequence counter (0 to 255):

$$\Delta \text{seq} = (\text{seq}_{\text{curr}} - \text{seq}_{\text{last}} - 1) \pmod{256}$$

* **Rollover Invariance:** Handles the 255 to 0 unsigned wrapping without false drop alerts.
* **Duplicate & Delay Gating:** Uses an acceptance window ($0 < \Delta \text{seq} < 50$) to reject duplicate frames and severely delayed packets from distorting cumulative loss statistics.

### Mission-Critical Command Interlocks

* **Authoritative Vehicle State:** Follows flight software interlock standards. Local UI state never mutates optimistically upon command dispatch.
* **Telemetry Bitmask Verification:** Dispatching `/api/command/arm` transmits a `MAV_CMD_COMPONENT_ARM_DISARM` long packet. The system only reports `ARMED` once the flight computer echoes confirmation via the `MAV_MODE_FLAG_SAFETY_ARMED` (`0x80`) bitmask in downlinked `HEARTBEAT` messages.

### Primary Flight Display & Tactical GIS

* **Attitude Director Indicator (ADI):** Vector-based artificial horizon drawn in pure SVG, dynamically calculating pitch ladder translations and roll angles in real time.
* **Tactical Moving Map:** Leaflet.js engine integrated with CartoDB Dark Matter monochrome tiles, dynamic SVG heading chevrons, and rolling 150-coordinate flight breadcrumbs centered on Mojave Air and Space Port (35.0594° N, -118.1517° W).

### Native Synthetic Audio System

* **Zero Audio Asset Dependencies:** Generates dual-frequency caution alarms (750 Hz / 900 Hz alternating square waves) directly in browser memory via the Web Audio API (`AudioContext`, `OscillatorNode`, `GainNode`).
* **Heartbeat Watchdog:** Automatically triggers caution tones if packet arrival stalls exceed 1,200 ms or the socket connection closes.

---

## 3. Automated Verification Suite

Unit and integration tests run headlessly in isolated memory spaces using `pytest` and `pytest-asyncio`:

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

## 4. Directory Layout

```text
.
├── backend/
│   ├── app/
│   │   ├── config.py             # System & connection configuration
│   │   ├── main.py               # FastAPI routes, REST endpoints & WebSocket broadcaster
│   │   ├── schemas.py            # Pydantic telemetry models
│   │   └── vehicle.py            # UDP MAVLink ingestion loop & state tracking
│   ├── scripts/
│   │   └── mock_mavlink.py       # Kinematic flight sim & telemetry generator
│   └── tests/
│       ├── conftest.py           # Pytest fixtures & async HTTP test client
│       ├── test_api.py           # API health check verification
│       ├── test_command_interlocks.py  # Safety state machine tests
│       └── test_mavlink_integrity.py   # Modulo-256 math & packet drop tests
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ArtificialHorizon.vue # MIL-STD-1787C Primary Flight Display
    │   │   ├── ControlPanel.vue      # Command uplink buttons & safety interlocks
    │   │   ├── TacticalMap.vue       # Leaflet moving map with CartoDB dark tiles
    │   │   └── TelemetryCard.vue     # High-contrast instrumentation readouts
    │   ├── stores/
    │   │   └── vehicleStore.js       # Pinia reactive telemetry state
    │   ├── utils/
    │   │   └── audioCaution.js       # Native Web Audio API dual-tone synthesizer
    │   ├── App.vue                   # Dual-deck cockpit interface
    │   └── main.js
    └── package.json

```

---

## 5. Quickstart & Local Setup

### Prerequisites

* Python 3.11+
* Node.js 18+ & npm

### Step 1: Backend Service

```bash
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

Open `http://localhost:5173` in your browser.

### Step 3: Flight Telemetry Simulator (HIL Stream)

In a separate terminal, launch the mock kinematics script:

```bash
cd backend
# With virtual environment active:
python scripts/mock_mavlink.py

```

---

## 6. Hardware & Simulation Compatibility

The ingestion engine binds to standard UDP port `14550` using MAVLink 2.0 framing, providing drop-in compatibility with:

* **ArduPilot SITL / PX4 SITL:** Software-in-the-loop simulation (`sim_vehicle.py -v ArduCopter --out=udp:127.0.0.1:14550`)
* **Physical Pixhawk / Cube Flight Controllers:** Connected via USB or telemetry radios through a serial-to-UDP bridge (`mavproxy.py --master="COM3" --baudrate=115200 --out=udp:127.0.0.1:14550`)
* **HIL Benches:** Benchtop telemetry links operating over SiK 915 MHz or RFD900 transceivers.

---

## 7. Technical Interview Architecture Defense (Cheat Sheet)

### UDP vs. TCP for Flight Telemetry

TCP enforces strict in-order delivery through retransmission. Over degraded or high-latency RF links, this introduces **Head-of-Line (HoL) blocking**, where fresh attitude updates are paused while waiting for retransmissions of stale packets. Telemetry is ephemeral; an attitude packet that is 200 ms late is useless to ground operators. The GCS prioritizes the newest frame over complete recovery, making non-blocking UDP the correct transport.

### Prevention of Optimistic UI State

Optimistic updates in aerospace ground software can create dangerous discrepancies between displayed and actual vehicle states. If a ground station marks an engine as "ARMED" before receiving verification, operators may act on false assumptions during an abort. Ground software must remain strictly authoritative, reflecting armed status only after receiving downlinked confirmation through the `MAV_MODE_FLAG_SAFETY_ARMED` (`0x80`) bitmask.

### Unproxied Leaflet Lifecycle in Vue 3

Wrapping third-party DOM-manipulating libraries like Leaflet inside Vue 3's reactive proxies (`ref` or `reactive`) intercepts internal prototype methods, map events, and container coordinates. This leads to memory leaks and rendering freezes during high-frequency map updates. Keeping map and marker instances as plain, unproxied JavaScript variables guarantees clean teardowns and reliable rendering.

---

## 9. License

```text
MIT License

Copyright (c) 2026 Preston Thurman Foote

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```

```

```
