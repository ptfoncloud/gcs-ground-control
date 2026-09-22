<template>
  <div class="recorder-panel">
    <div class="recorder-label">
      <span>BLACKBOX RECORDER</span>
      <span class="recorder-status" :class="{ active: status.is_recording }">
        {{ status.is_recording ? `RECORDING (${status.frames_captured} FRAMES)` : 'STANDBY' }}
      </span>
    </div>
    <div class="recorder-buttons">
      <button class="deck-btn rec-btn" :disabled="status.is_recording" @click="startRecord">REC</button>
      <button class="deck-btn export-btn" :disabled="!status.is_recording" @click="stopAndDownload">STOP & CSV</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { API_BASE_URL } from '../config'

const status = ref({ is_recording: false, frames_captured: 0 })
let pollInterval = null

async function refreshStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/record/status`)
    status.value = await res.json()
  } catch (err) {
    console.error('Failed to fetch recorder status:', err)
  }
}

async function startRecord() {
  try {
    await fetch(`${API_BASE_URL}/api/record/start`, { method: 'POST' })
    await refreshStatus()
  } catch (err) {
    console.error('Failed to start recording:', err)
  }
}

async function stopAndDownload() {
  try {
    await fetch(`${API_BASE_URL}/api/record/stop`, { method: 'POST' })
    window.open(`${API_BASE_URL}/api/record/export`, '_blank')
    await refreshStatus()
  } catch (err) {
    console.error('Failed to stop recording:', err)
  }
}

onMounted(() => {
  refreshStatus()
  pollInterval = setInterval(refreshStatus, 1000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<style scoped>
.recorder-panel {
  background: #09090b;
  border: 1px solid #27272a;
  border-top: 3px solid #52525b;
  padding: 12px 18px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.recorder-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: #71717a;
}

.recorder-status {
  color: #52525b;
}

.recorder-status.active {
  color: #ef4444;
}

.recorder-buttons {
  display: flex;
  gap: 8px;
}

.deck-btn {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 6px 12px;
  border-radius: 2px;
  cursor: pointer;
  border: 1px solid #3f3f46;
  background: #18181b;
  color: #d4d4d8;
  transition: all 0.15s ease;
}

.deck-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.deck-btn:hover:not(:disabled) {
  background: #27272a;
  border-color: #71717a;
  color: #ffffff;
}

.rec-btn:active:not(:disabled) {
  background: #7f1d1d;
  border-color: #ef4444;
}

.export-btn:active:not(:disabled) {
  background: #14532d;
  border-color: #22c55e;
}
</style>
