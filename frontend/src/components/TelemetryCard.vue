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

    <div class="card-footer-rail">
      <div class="card-sublabel">{{ sublabel || 'NOMINAL' }}</div>
    </div>
  </div>
</template>

<script setup>
// Pure display component — the recorder controls used to be duplicated
// here (once per card instance, 4x on screen). They now live once in
// RecorderControls.vue.
defineProps({
  channel: { type: String, default: 'CH-00' },
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  unit: { type: String, default: '' },
  sublabel: { type: String, default: '' },
  isAlert: { type: Boolean, default: false }
})
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
  min-height: 120px;
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
