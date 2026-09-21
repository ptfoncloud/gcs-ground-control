<template>
  <div class="deck-container">
    <div class="deck-header">
      <div class="deck-branding">
        <span class="deck-subsystem">SYS-01 // UPLINK</span>
        <span class="deck-title">COMMAND & CONTROL DECK</span>
      </div>
      <div class="interlock-pill" :class="{ 'armed-state': store.telemetry.armed }">
        <span class="hazard-indicator"></span>
        {{ store.telemetry.armed ? 'PROPULSION ARMED' : 'VEHICLE DISARMED' }}
      </div>
    </div>

    <div class="deck-grid">
      <div class="control-box">
        <div class="box-label">
          <span>INTERLOCK 01</span>
          <span>PROPULSION IGNITION</span>
        </div>
        <button
          class="btn-action"
          :class="{ 'btn-hazard': store.telemetry.armed, 'btn-arm': !store.telemetry.armed }"
          :disabled="isTransmitting"
          @click="toggleArm"
        >
          <span class="btn-text">
            {{ isTransmitting ? 'TRANSMITTING...' : store.telemetry.armed ? 'FORCE DISARM' : 'ARM PROPULSION' }}
          </span>
          <span class="btn-annotation">
            {{ store.telemetry.armed ? 'SAFETY HAZARD ACTIVE' : 'SYSTEM STANDBY' }}
          </span>
        </button>
      </div>

      <div class="control-box">
        <div class="box-label">
          <span>NAV-02</span>
          <span>AUTOPILOT FLIGHT MODE (ACTIVE: {{ store.telemetry.flight_mode }})</span>
        </div>
        <div class="mode-action-row">
          <select v-model="selectedMode" class="mode-select">
            <option v-for="mode in availableModes" :key="mode" :value="mode">
              {{ mode }}
            </option>
          </select>
          <button
            class="btn-mode-commit"
            :disabled="isTransmitting"
            @click="setFlightMode"
          >
            COMMIT MODE
          </button>
        </div>
      </div>
    </div>

    <div v-if="statusFeedback" class="uplink-log">
      <span class="log-indicator">></span>
      <span class="log-msg">{{ statusFeedback }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useVehicleStore } from '../stores/vehicleStore'

const store = useVehicleStore()
const availableModes = ['GUIDED', 'AUTO', 'RTL', 'LOITER', 'STABILIZE']
const selectedMode = ref('GUIDED')
const isTransmitting = ref(false)
const statusFeedback = ref('')

let feedbackTimer = null

const setTimedFeedback = (message, durationMs = 4000) => {
  if (feedbackTimer) clearTimeout(feedbackTimer)
  statusFeedback.value = message
  feedbackTimer = setTimeout(() => {
    statusFeedback.value = ''
    feedbackTimer = null
  }, durationMs)
}

onUnmounted(() => {
  if (feedbackTimer) clearTimeout(feedbackTimer)
})

const sendCommand = async (payload) => {
  isTransmitting.value = true
  try {
    const response = await fetch('http://localhost:8080/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    setTimedFeedback(`ACK_RX: ${data.detail || payload.command} [COMMAND_ACCEPTED]`)
  } catch (err) {
    setTimedFeedback(`ACK_ERR: UPLINK_FAILURE (${err.message})`)
  } finally {
    isTransmitting.value = false
  }
}

const toggleArm = () => {
  const targetCommand = store.telemetry.armed ? 'DISARM' : 'ARM'
  sendCommand({ command: targetCommand })
}

const setFlightMode = () => {
  sendCommand({ command: 'SET_MODE', mode: selectedMode.value })
}
</script>

<style scoped>
.deck-container {
  background: #09090b;
  border: 1px solid #27272a;
  border-top: 3px solid #71717a;
  padding: 18px 22px;
  margin-bottom: 24px;
  box-sizing: border-box;
}

.deck-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #18181b;
  padding-bottom: 14px;
  margin-bottom: 18px;
}

.deck-branding {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.deck-subsystem {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #71717a;
}

.deck-title {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.95rem;
  font-weight: 900;
  letter-spacing: 0.15em;
  color: #ffffff;
}

.interlock-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border: 1px solid #3f3f46;
  background: #18181b;
  color: #a1a1aa;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.interlock-pill.armed-state {
  border-color: #ef4444;
  background: #360808;
  color: #fca5a5;
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
}

.hazard-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.deck-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 800px) {
  .deck-grid {
    grid-template-columns: 1fr;
  }
}

.control-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.box-label {
  display: flex;
  justify-content: space-between;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #71717a;
}

.btn-action {
  height: 52px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: none;
  cursor: pointer;
  transition: opacity 0.1s;
  box-sizing: border-box;
}

.btn-arm {
  background: #ffffff;
  color: #000000;
}

.btn-arm:hover:not(:disabled) {
  background: #e4e4e7;
}

.btn-hazard {
  background: #ef4444;
  color: #ffffff;
}

.btn-hazard:hover:not(:disabled) {
  background: #dc2626;
}

.btn-action:disabled, .btn-mode-commit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-text {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.95rem;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.btn-annotation {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  opacity: 0.75;
  margin-top: 2px;
}

.mode-action-row {
  display: flex;
  gap: 10px;
  height: 52px;
}

.mode-select {
  flex: 1;
  background: #18181b;
  border: 1px solid #3f3f46;
  color: #ffffff;
  padding: 0 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  outline: none;
}

.mode-select:focus {
  border-color: #ffffff;
}

.btn-mode-commit {
  padding: 0 22px;
  background: #27272a;
  border: 1px solid #3f3f46;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.85rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  cursor: pointer;
}

.btn-mode-commit:hover:not(:disabled) {
  background: #3f3f46;
}

.uplink-log {
  margin-top: 16px;
  padding: 10px 14px;
  background: #111113;
  border-left: 3px solid #38bdf8;
  display: flex;
  gap: 10px;
  align-items: center;
}

.log-indicator {
  color: #38bdf8;
  font-family: "Consolas", "SF Mono", monospace;
  font-weight: 800;
}

.log-msg {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.8rem;
  font-weight: 700;
  color: #e4e4e7;
  letter-spacing: 0.04em;
}
</style>
