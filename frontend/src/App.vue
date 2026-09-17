<template>
  <div class="console-layout">
    <header>
      <h1>MISSION OPERATIONS CONSOLE</h1>
      <div class="status-pill" :class="{ online: store.connected }">
        {{ store.connected ? 'LINK ACTIVE' : 'DISCONNECTED' }}
      </div>
    </header>
    <main>
      <pre>{{ store.telemetry }}</pre>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useVehicleStore } from './stores/vehicleStore'

const store = useVehicleStore()
let ws = null

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
  padding: 20px;
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
  padding-bottom: 12px;
}

h1 {
  font-size: 1.1rem;
  letter-spacing: 0.05em;
  color: #38bdf8;
  margin: 0;
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

pre {
  margin-top: 20px;
  padding: 16px;
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 6px;
  color: #4ade80;
  font-size: 0.8rem;
  overflow-x: auto;
}
</style>
