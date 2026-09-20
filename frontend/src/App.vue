<template>
  <div class="console-layout">
    <header>
      <div>
        <h1>MISSION OPERATIONS CONSOLE</h1>
        <p class="subtitle">AUTONOMOUS FLIGHT CORE v1.0.0</p>
      </div>
      <div class="status-pill" :class="{ online: store.connected }">
        {{ store.connected ? 'LINK ACTIVE' : 'DISCONNECTED' }}
      </div>
    </header>

    <main>
      <!-- Telemetry Gauges Grid -->
      <div class="gauge-grid">
        <TelemetryCard label="Altitude AGL" :value="store.telemetry.altitude.toFixed(1)" unit="m" />
        <TelemetryCard label="Ground Speed" :value="store.telemetry.ground_speed.toFixed(1)" unit="m/s" />
        <TelemetryCard label="Battery Rail" :value="store.telemetry.battery_voltage.toFixed(2)" unit="V" />
        <TelemetryCard label="Pitch" :value="toDegrees(store.telemetry.pitch)" unit="deg" />
        <TelemetryCard label="Roll" :value="toDegrees(store.telemetry.roll)" unit="deg" />
        <TelemetryCard label="Heading" :value="formatHeading(store.telemetry.yaw)" unit="deg" />
      </div>

      <!-- Collapsible Raw Feed -->
      <details>
        <summary>Raw Ingest Stream</summary>
        <pre>{{ store.telemetry }}</pre>
      </details>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useVehicleStore } from './stores/vehicleStore'
import TelemetryCard from './components/TelemetryCard.vue'

const store = useVehicleStore()
let ws = null

// Conversion helpers
const toDegrees = (rad) => ((rad * 180) / Math.PI).toFixed(1)
const formatHeading = (yawRad) => {
  let deg = (yawRad * 180) / Math.PI
  if (deg < 0) deg += 360
  return deg.toFixed(0)
}

onMounted(() => {
  ws = new WebSocket('ws://localhost:8080/ws/telemetry')

  ws.onopen = () => {
    store.connected = true
  }

  ws.onmessage = (event) => {
    try {
      store.updateTelemetry(JSON.parse(event.data))
    } catch (err) {
      console.error('Failed to parse telemetry packet:', err)
    }
  }

  ws.onclose = () => {
    store.connected = false
  }
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.console-layout {
  padding: 24px;
  font-family: monospace;
  background-color: #020617;
  color: #f8fafc;
  min-height: 100vh;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #334155;
  padding-bottom: 14px;
  margin-bottom: 24px;
}

h1 {
  font-size: 1.15rem;
  letter-spacing: 0.05em;
  color: #38bdf8;
  margin: 0;
}

.subtitle {
  font-size: 0.7rem;
  color: #64748b;
  margin: 2px 0 0 0;
}

.status-pill {
  padding: 4px 10px;
  border-radius: 4px;
  background: #7f1d1d;
  color: #fca5a5;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.status-pill.online {
  background: #14532d;
  color: #86efac;
}

.gauge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

details {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 12px;
}

summary {
  cursor: pointer;
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  user-select: none;
}

pre {
  margin-top: 10px;
  padding: 12px;
  background: #020617;
  border: 1px solid #1e293b;
  border-radius: 4px;
  color: #4ade80;
  font-size: 0.75rem;
  overflow-x: auto;
}
</style>