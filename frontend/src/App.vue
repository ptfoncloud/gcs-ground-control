<template>
  <div class=""console-layout"">
    <header>
      <h1>MISSION OPERATIONS CONSOLE</h1>
      <div class=""status-pill"" :class=""{ online: store.connected }"">
        {{ store.connected ? 'LINK ACTIVE' : 'DISCONNECTED' }}
      </div>
    </header>
    <main>
      <!-- Telemetry Dashboard, Map, and Command Panels will mount here -->
      <pre>{{ store.telemetry }}</pre>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useVehicleStore } from './stores/vehicleStore'

const store = useVehicleStore()

onMounted(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/telemetry')
  ws.onmessage = (event) => {
    store.updateTelemetry(JSON.parse(event.data))
  }
})
</script>

<style scoped>
.console-layout { padding: 20px; }
header { display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 12px; }
.status-pill { padding: 4px 10px; border-radius: 4px; background: #ef4444; }
.status-pill.online { background: #22c55e; }
</style>
