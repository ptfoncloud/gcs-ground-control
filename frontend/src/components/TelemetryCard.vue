<template>
  <div class="telemetry-card" :class="{ 'card-alert': isAlert }">
    <div class="card-meta-row">
      <span class="card-channel">{{ channel }}</span>
      <span class="card-status-dot"></span>
    </div>

    <div class="card-label">{{ label }}</div>

    <div class="card-value-cluster">
      <span class="card-value">{{ value }}</span>
      <span class="card-unit">{{ unit }}</span>
    </div>

    <div class="recorder-deck">
      <button class="deck-btn rec-btn" @click="startRecord">REC</button>
      <button class="deck-btn export-btn" @click="stopAndDownload">STOP & CSV</button>
    </div>

    <div class="card-footer-rail">
      <div class="card-sublabel">{{ sublabel || 'NOMINAL' }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  channel: { type: String, default: 'CH-00' },
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  unit: { type: String, default: '' },
  sublabel: { type: String, default: '' },
  isAlert: { type: Boolean, default: false }
})

async function startRecord() {
  try {
    await fetch("http://localhost:8080/api/record/start", { method: "POST" });
  } catch (err) {
    console.error("Failed to start recording:", err);
  }
}

async function stopAndDownload() {
  try {
    await fetch("http://localhost:8080/api/record/stop", { method: "POST" });
    window.open("http://localhost:8080/api/record/export", "_blank");
  } catch (err) {
    console.error("Failed to stop recording:", err);
  }
}
</script>

<style scoped>
.telemetry-card {
  background: #09090b;
  border: 1px solid #27272a;
  border-top: 3px solid #52525b;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 155px;
  box-sizing: border-box;
  position: relative;
}

.telemetry-card.card-alert {
  border-top-color: #ef4444;
  background: #110505;
}

.card-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.card-channel {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #71717a;
}

.card-status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #22c55e;
}

.card-alert .card-status-dot {
  background: #ef4444;
}

.card-label {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #a1a1aa;
  text-transform: uppercase;
  margin-bottom: 10px;
}

.card-value-cluster {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.card-value {
  font-family: "Consolas", "SF Mono", "Roboto Mono", monospace;
  font-size: 2.8rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 0.95;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.card-unit {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.95rem;
  font-weight: 800;
  color: #71717a;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.recorder-deck {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.deck-btn {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 4px 8px;
  border-radius: 2px;
  cursor: pointer;
  border: 1px solid #3f3f46;
  background: #18181b;
  color: #d4d4d8;
  transition: all 0.15s ease;
}

.deck-btn:hover {
  background: #27272a;
  border-color: #71717a;
  color: #ffffff;
}

.rec-btn:active {
  background: #7f1d1d;
  border-color: #ef4444;
}

.export-btn:active {
  background: #14532d;
  border-color: #22c55e;
}

.card-footer-rail {
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid #18181b;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-sublabel {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #52525b;
  text-transform: uppercase;
}
</style>