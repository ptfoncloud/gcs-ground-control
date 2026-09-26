<template>
  <div class="gesture-panel">
    <div class="panel-header">
      <span class="panel-title">GESTURE UPLINK</span>
      <span class="sub-label">LEAP MOTION / HAND TRACKING</span>
    </div>

    <div class="status-row">
      <div class="status-pill" :class="{ ok: leapConnected }">
        LEAP: {{ leapConnected ? 'TRACKING' : 'NO DEVICE' }}
      </div>
      <div class="status-pill" :class="{ ok: wsConnected }">
        UPLINK: {{ wsConnected ? 'CONNECTED' : 'DISCONNECTED' }}
      </div>
    </div>

    <div v-if="lastCommand" class="last-command">
      <span class="dot">●</span>
      LAST GESTURE COMMAND: {{ lastCommand.command }}
      <span v-if="lastCommand.mode"> ({{ lastCommand.mode }})</span>
    </div>

    <div class="hint">
      Open palm, hold ~0.5s = LOITER &nbsp;·&nbsp; Fist, hold ~0.5s = RTL
      &nbsp;·&nbsp; Pinch, hold ~0.5s = ARM &nbsp;·&nbsp; Fast swipe = RTL
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { WS_BASE_URL } from '../config'

const leapConnected = ref(false)
const wsConnected = ref(false)
const lastCommand = ref(null)

const SEND_HZ = 20
const SEND_INTERVAL_MS = 1000 / SEND_HZ

let leapController = null
let gestureSocket = null
let lastSendMs = 0

function connectGestureSocket() {
  gestureSocket = new WebSocket(`${WS_BASE_URL}/ws/gestures`)

  gestureSocket.onopen = () => { wsConnected.value = true }
  gestureSocket.onclose = () => { wsConnected.value = false }
  gestureSocket.onerror = () => { wsConnected.value = false }

  gestureSocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.event === 'command_triggered') {
        lastCommand.value = data
        setTimeout(() => {
          if (lastCommand.value === data) lastCommand.value = null
        }, 3000)
      }
    } catch {
      // non-JSON or unexpected payload - ignore, not fatal to the connection
    }
  }
}

function countExtendedFingers(hand) {
  let count = 0
  for (let i = 0; i < hand.fingers.length; i++) {
    if (hand.fingers[i].extended) count++
  }
  return count
}

function onLeapFrame(frame) {
  leapConnected.value = frame.hands.length > 0

  if (frame.hands.length === 0) return

  const now = performance.now()
  if (now - lastSendMs < SEND_INTERVAL_MS) return
  lastSendMs = now

  if (gestureSocket?.readyState !== WebSocket.OPEN) return

  const hand = frame.hands[0]

  const payload = {
    palm_position: hand.palmPosition,
    palm_velocity: hand.palmVelocity,
    grab_strength: hand.grabStrength,
    pinch_strength: hand.pinchStrength,
    extended_fingers: countExtendedFingers(hand),
  }

  gestureSocket.send(JSON.stringify(payload))
}

onMounted(() => {
  connectGestureSocket()
  leapController = Leap.loop(onLeapFrame)
})

onUnmounted(() => {
  leapController?.disconnect()
  gestureSocket?.close()
})
</script>

<style scoped>
.gesture-panel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 18px;
  margin-bottom: 24px;
  font-family: monospace;
}

.panel-header {
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 12px;
  margin-bottom: 14px;
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

.status-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.status-pill {
  padding: 4px 10px;
  border-radius: 4px;
  background: #1e293b;
  color: #94a3b8;
  font-size: 0.7rem;
  font-weight: 700;
}

.status-pill.ok {
  background: #064e3b;
  color: #6ee7b7;
}

.last-command {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: #4ade80;
  margin-bottom: 10px;
}

.hint {
  font-size: 0.65rem;
  color: #64748b;
  line-height: 1.5;
}
</style>