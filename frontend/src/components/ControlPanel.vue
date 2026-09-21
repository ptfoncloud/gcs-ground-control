<template>
  <div class="control-panel">
    <div class="panel-header">
      <div class="title-group">
        <span class="panel-title">FLIGHT COMMAND LINK</span>
        <span class="sub-label">UPLINK PORT: 8080 / TARGET: SYS 1</span>
      </div>
      <div class="state-pill" :class="{ armed: store.telemetry.armed }">
        {{ store.telemetry.armed ? 'ARMED' : 'DISARMED' }}
      </div>
    </div>

    <div class="controls-grid">
      <div class="control-card">
        <span class="control-label">Propulsion State</span>
        <button
          v-if="!store.telemetry.armed"
          class="btn btn-arm"
          :disabled="!store.connected || isTransmitting"
          @click="sendCommand('ARM')"
        >
          {{ isTransmitting ? 'TRANSMITTING...' : 'ARM PROPULSION' }}
        </button>
        <button
          v-else
          class="btn btn-disarm"
          :disabled="!store.connected || isTransmitting"
          @click="sendCommand('DISARM')"
        >
          {{ isTransmitting ? 'TRANSMITTING...' : 'FORCE DISARM' }}
        </button>
      </div>

      <div class="control-card">
        <span class="control-label">
          Mode Ingest (Active: {{ store.telemetry.flight_mode || 'UNKNOWN' }})
        </span>
        <div class="mode-input-row">
          <select
            v-model="selectedMode"
            :disabled="!store.connected || isTransmitting"
            class="mode-select"
          >
            <option value="GUIDED">GUIDED</option>
            <option value="AUTO">AUTO</option>
            <option value="RTL">RTL</option>
            <option value="LOITER">LOITER</option>
            <option value="STABILIZE">STABILIZE</option>
          </select>
          <button
            class="btn btn-mode"
            :disabled="!store.connected || isTransmitting"
            @click="sendCommand('SET_MODE', selectedMode)"
          >
            {{ isTransmitting ? 'TRANSMITTING...' : 'SET MODE' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="statusFeedback" class="status-feed" :class="{ error: isError }">
      <span class="dot">●</span>
      <span class="status-msg">{{ statusFeedback }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useVehicleStore } from '../stores/vehicleStore'

const store = useVehicleStore()
const selectedMode = ref('GUIDED')
const isTransmitting = ref(false)
const statusFeedback = ref('')
const isError = ref(false)

let feedbackTimer = null

const BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080'

const setTimedFeedback = (message, durationMs = 3000) => {
  if (feedbackTimer) clearTimeout(feedbackTimer)
  statusFeedback.value = message
  feedbackTimer = setTimeout(() => {
    statusFeedback.value = ''
    feedbackTimer = null
  }, durationMs)
}

const sendCommand = async (command, mode = null) => {
  if (feedbackTimer) {
    clearTimeout(feedbackTimer)
    feedbackTimer = null
  }

  isTransmitting.value = true
  isError.value = false
  statusFeedback.value = `TRANSMITTING ${command}...`

  try {
    const payload = { command }
    if (mode) payload.mode = mode

    const response = await fetch(`${BASE}/api/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || `HTTP ${response.status}`)
    }

    const data = await response.json()
    setTimedFeedback(`UPLINK ACKNOWLEDGED: ${data.dispatched}`)
  } catch (err) {
    isError.value = true
    statusFeedback.value = `UPLINK FAILED: ${err.message}`
  } finally {
    isTransmitting.value = false
  }
}

onUnmounted(() => {
  if (feedbackTimer) clearTimeout(feedbackTimer)
})
</script>

<style scoped>
.control-panel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 18px;
  margin-bottom: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.title-group {
  display: flex;
  flex-direction: column;
}

.panel-title {
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  color: #38bdf8;
  font-weight: 700;
}

.sub-label {
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 2px;
}

.state-pill {
  padding: 3px 8px;
  border-radius: 4px;
  background: #1e293b;
  color: #94a3b8;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.state-pill.armed {
  background: #7f1d1d;
  color: #fca5a5;
  border: 1px solid #ef4444;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.control-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-label {
  font-size: 0.7rem;
  color: #94a3b8;
  text-transform: uppercase;
}

.mode-input-row {
  display: flex;
  gap: 8px;
}

.mode-select {
  flex: 1;
  background: #020617;
  border: 1px solid #334155;
  border-radius: 4px;
  color: #f8fafc;
  padding: 8px;
  font-family: monospace;
  font-size: 0.8rem;
  outline: none;
}

.mode-select:focus {
  border-color: #38bdf8;
}

.btn {
  padding: 8px 14px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s ease;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-arm {
  background: #059669;
  color: #ecfdf5;
}

.btn-arm:not(:disabled):hover {
  background: #10b981;
}

.btn-disarm {
  background: #b91c1c;
  color: #fef2f2;
}

.btn-disarm:not(:disabled):hover {
  background: #dc2626;
}

.btn-mode {
  background: #0284c7;
  color: #f0f9ff;
  white-space: nowrap;
}

.btn-mode:not(:disabled):hover {
  background: #38bdf8;
}

.status-feed {
  margin-top: 14px;
  padding: 8px 12px;
  background: #020617;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: #4ade80;
}

.status-feed.error {
  color: #f87171;
}

.dot {
  font-size: 0.65rem;
}
</style>