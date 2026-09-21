<!-- frontend/src/App.vue -->
<template>
  <div class="mission-screen">
    <!-- TOP FLIGHT HEADER BAR -->
    <header class="mission-header">
      <div class="header-left">
        <div class="brand-title">MISSION OPERATIONS CONSOLE</div>
        <div class="meta-row">
          <span class="meta-item">PROGRAM: AUTONOMOUS FLIGHT CORE</span>
          <span class="meta-sep">//</span>
          <span class="meta-item">SYS 01</span>
          <span class="meta-sep">//</span>
          <span class="meta-item">PORT 14550</span>
        </div>
      </div>

      <div class="header-center">
        <div class="clock-label">MISSION ELAPSED TIME (UTC)</div>
        <div class="clock-display">{{ utcTimeStr }}</div>
      </div>

      <div class="header-right">
        <!-- Audio Safety Toggle -->
        <button 
          class="audio-toggle-btn" 
          :class="{ muted: isAudioMuted }"
          @click="handleAudioToggle"
        >
          AUDIO: {{ isAudioMuted ? 'MUTED' : 'ARMED' }}
        </button>

        <!-- Live Watchdog & Packet Integrity Cluster -->
        <div class="watchdog-cluster">
          <div class="watchdog-rate-row">
            <span class="watchdog-rate">{{ packetRateHz.toFixed(1) }} HZ</span>
            <span class="loss-rate" :class="{ 'has-loss': (store.telemetry.packet_loss_pct || 0) > 0 }">
              LOSS: {{ (store.telemetry.packet_loss_pct || 0).toFixed(2) }}%
            </span>
          </div>
          <span class="watchdog-sub">
            RX: {{ (store.telemetry.packets_rx || 0).toLocaleString() }} PKTS
          </span>
        </div>

        <!-- Master Link Status Badge -->
        <div 
          class="link-badge" 
          :class="{ 
            'link-nominal': store.connected && isLinkFresh, 
            'link-stale': store.connected && !isLinkFresh 
          }"
        >
          <span class="link-pip"></span>
          {{ !store.connected ? 'LINK LOSS' : isLinkFresh ? 'CARRIER LOCK' : 'DATA STALE' }}
        </div>
      </div>
    </header>

    <!-- MAIN COCKPIT WORKSPACE -->
    <main class="console-body">
      <ControlPanel />

      <!-- UPPER DECK: PFD + MOVING MAP -->
      <div class="flight-deck-grid">
        <div class="deck-panel pfd-container">
          <ArtificialHorizon 
            :pitch-rad="store.telemetry.pitch" 
            :roll-rad="store.telemetry.roll" 
          />
        </div>

        <div class="deck-panel map-container">
          <TacticalMap 
            :lat="store.telemetry.lat || 35.0594" 
            :lon="store.telemetry.lon || -118.1517" 
            :heading-deg="getHeadingDeg()" 
          />
        </div>
      </div>

      <!-- LOWER DECK: 4-COLUMN HORIZONTAL TELEMETRY RAIL -->
      <div class="telemetry-rail">
        <TelemetryCard 
          channel="NAV-01"
          label="Altitude AGL" 
          :value="store.telemetry.altitude.toFixed(1)" 
          unit="M" 
          sublabel="RADAR ALTIMETER"
        />
        <TelemetryCard 
          channel="NAV-02"
          label="Ground Speed" 
          :value="store.telemetry.ground_speed.toFixed(1)" 
          unit="M/S" 
          sublabel="DOPPLER KINEMATICS"
        />
        <TelemetryCard 
          channel="PWR-01"
          label="Battery Rail" 
          :value="store.telemetry.battery_voltage.toFixed(2)" 
          unit="V" 
          sublabel="MAIN BUS 4S"
          :is-alert="store.telemetry.battery_voltage < 11.1"
        />
        <TelemetryCard 
          channel="DIR-01"
          label="Heading" 
          :value="formatHeading(store.telemetry.yaw)" 
          unit="DEG" 
          sublabel="MAGNETIC NORTH"
        />
      </div>

      <!-- BITSTREAM INSPECTOR -->
      <details class="telemetry-drawer">
        <summary class="drawer-toggle">
          <span>DOWNLINK BITSTREAM INSPECTOR (JSON)</span>
          <span class="toggle-hint">[EXPAND RAW FEED]</span>
        </summary>
        <pre class="stream-dump">{{ store.telemetry }}</pre>
      </details>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useVehicleStore } from './stores/vehicleStore'
import { startAlarm, stopAlarm, toggleMute } from './utils/audioCaution'
import TelemetryCard from './components/TelemetryCard.vue'
import ControlPanel from './components/ControlPanel.vue'
import ArtificialHorizon from './components/ArtificialHorizon.vue'
import TacticalMap from './components/TacticalMap.vue'

const store = useVehicleStore()
let ws = null

// Clock
const utcTimeStr = ref('00:00:00 UTC')
let clockInterval = null

// Packet tracking & link watchdog
const packetRateHz = ref(0.0)
const isLinkFresh = ref(false)
let packetTimes = []
let watchdogInterval = null
let lastPacketsRx = -1
let lastPacketTime = performance.now()

// Audio mute state
const isAudioMuted = ref(false)
const handleAudioToggle = () => {
  isAudioMuted.value = toggleMute()
}

// Master caution watchdog trigger
watch([() => store.connected, isLinkFresh], ([connected, fresh]) => {
  if (!connected || !fresh) {
    startAlarm()
  } else {
    stopAlarm()
  }
})

const getHeadingDeg = () => {
  let deg = (store.telemetry.yaw * 180) / Math.PI
  if (deg < 0) deg += 360
  return deg
}

const formatHeading = (yawRad) => {
  return getHeadingDeg().toFixed(0)
}

onMounted(() => {
  clockInterval = setInterval(() => {
    const now = new Date()
    utcTimeStr.value = now.toUTCString().split(' ')[4] + ' UTC'
  }, 1000)

  // Watchdog checks every 250ms for telemetry stall (>1.2s)
  watchdogInterval = setInterval(() => {
    const now = performance.now()
    packetTimes = packetTimes.filter(t => now - t <= 1000)
    packetRateHz.value = packetTimes.length

    if (now - lastPacketTime > 1200) {
      isLinkFresh.value = false
    }
  }, 250)

  ws = new WebSocket('ws://localhost:8080/ws/telemetry')

  ws.onopen = () => {
    store.connected = true
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      store.updateTelemetry(data)

      // Confirm packets_rx increments before counting frame as fresh
      if (data.packets_rx && data.packets_rx > lastPacketsRx) {
        lastPacketsRx = data.packets_rx
        lastPacketTime = performance.now()
        packetTimes.push(performance.now())
        isLinkFresh.value = true
      }
    } catch (err) {
      console.error('Failed to parse telemetry packet:', err)
    }
  }

  ws.onclose = () => {
    store.connected = false
    isLinkFresh.value = false
  }
})

onUnmounted(() => {
  if (ws) ws.close()
  if (clockInterval) clearInterval(clockInterval)
  if (watchdogInterval) clearInterval(watchdogInterval)
  stopAlarm()
})
</script>

<style scoped>
.mission-screen {
  padding: 20px 28px;
  background-color: #000000;
  color: #ffffff;
  min-height: 100vh;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.mission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #27272a;
  padding-bottom: 14px;
  margin-bottom: 18px;
}

.brand-title {
  font-size: 1.25rem;
  font-weight: 900;
  letter-spacing: 0.16em;
  color: #ffffff;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.meta-item {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #71717a;
}

.meta-sep {
  color: #3f3f46;
  font-size: 0.7rem;
}

.header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.clock-label {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #71717a;
}

.clock-display {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #ffffff;
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.audio-toggle-btn {
  background: #18181b;
  border: 1px solid #3f3f46;
  color: #e4e4e7;
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 6px 12px;
  cursor: pointer;
}

.audio-toggle-btn.muted {
  border-color: #71717a;
  color: #71717a;
  background: #09090b;
}

.watchdog-cluster {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.watchdog-rate-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.watchdog-rate {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.95rem;
  font-weight: 800;
  color: #38bdf8;
  font-variant-numeric: tabular-nums;
}

.loss-rate {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.75rem;
  font-weight: 700;
  color: #71717a;
}

.loss-rate.has-loss {
  color: #ef4444;
}

.watchdog-sub {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #52525b;
}

.link-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border: 1px solid #7f1d1d;
  background: #360808;
  color: #fca5a5;
  font-size: 0.8rem;
  font-weight: 900;
  letter-spacing: 0.12em;
}

.link-badge.link-nominal {
  border-color: #15803d;
  background: #052e16;
  color: #86efac;
}

.link-badge.link-stale {
  border-color: #ca8a04;
  background: #362505;
  color: #fde047;
}

.link-pip {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* UPPER DECK: PFD + MAP SIDE-BY-SIDE */
.flight-deck-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  align-items: stretch;
  margin-bottom: 16px;
}

.deck-panel {
  display: flex;
  flex-direction: column;
}

/* LOWER DECK: 4 GAUGES IN ONE ROW */
.telemetry-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

@media (max-width: 1024px) {
  .flight-deck-grid {
    grid-template-columns: 1fr;
  }
  .telemetry-rail {
    grid-template-columns: repeat(2, 1fr);
  }
}

.telemetry-drawer {
  background: #09090b;
  border: 1px solid #27272a;
  padding: 12px 16px;
}

.drawer-toggle {
  display: flex;
  justify-content: space-between;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #a1a1aa;
  user-select: none;
}

.toggle-hint {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.7rem;
  color: #52525b;
}

.stream-dump {
  margin-top: 12px;
  padding: 12px;
  background: #000000;
  border: 1px solid #18181b;
  color: #a1a1aa;
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.85rem;
  overflow-x: auto;
}
</style>