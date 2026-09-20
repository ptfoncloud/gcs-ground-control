<template>
  <div class="card">
    <span class="label">{{ label }}</span>
    <div class="value-row">
      <span class="value">{{ value }}</span>
      <span class="unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  unit: { type: String, default: '' }
})
</script>

<style scoped>
.card {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.label {
  font-size: 0.7rem;
  color: #94a3b8;
  text-transform: uppercase;
  font-weight: 600;
}
.value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 8px;
}
.value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #38bdf8;
}
.unit {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
}
</style>