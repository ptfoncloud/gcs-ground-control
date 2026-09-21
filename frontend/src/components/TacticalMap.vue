<!-- frontend/src/components/TacticalMap.vue -->
<template>
  <div class="map-card">
    <div class="map-header">
      <div class="map-title-row">
        <span class="subsystem-code">NAV-03</span>
        <span class="map-label">TACTICAL SITUATIONAL MAP</span>
      </div>
      <div class="coords-readout">
        <span>LAT: {{ lat.toFixed(5) }}°</span>
        <span class="sep">//</span>
        <span>LON: {{ lon.toFixed(5) }}°</span>
      </div>
    </div>
    <div ref="mapContainer" class="leaflet-viewport"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  lat: { type: Number, default: 35.0594 },
  lon: { type: Number, default: -118.1517 },
  headingDeg: { type: Number, default: 0 }
})

const mapContainer = ref(null)

let map = null
let vehicleMarker = null
let flightPath = null
const breadcrumbs = []

const createVehicleIcon = (heading) => {
  return L.divIcon({
    className: 'vehicle-marker-div',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    html: `
      <div style="transform: rotate(${heading}deg); transform-origin: 16px 16px; width: 32px; height: 32px;">
        <svg viewBox="0 0 32 32" width="32" height="32">
          <polygon points="16,2 28,28 16,22 4,28" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
          <circle cx="16" cy="16" r="2" fill="#000000" />
        </svg>
      </div>
    `
  })
}

onMounted(() => {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value, {
    center: [props.lat, props.lon],
    zoom: 14,
    zoomControl: false,
    attributionControl: false
  })

  // CartoDB Dark Matter monochrome tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd'
  }).addTo(map)

  flightPath = L.polyline([], {
    color: '#38bdf8',
    weight: 2,
    opacity: 0.8,
    dashArray: '4, 4'
  }).addTo(map)

  vehicleMarker = L.marker([props.lat, props.lon], {
    icon: createVehicleIcon(props.headingDeg)
  }).addTo(map)

  setTimeout(() => {
    map.invalidateSize()
  }, 200)
})

watch([() => props.lat, () => props.lon, () => props.headingDeg], ([newLat, newLon, newHeading]) => {
  if (!map || !vehicleMarker || (newLat === 0 && newLon === 0)) return

  const pos = [newLat, newLon]
  vehicleMarker.setLatLng(pos)
  vehicleMarker.setIcon(createVehicleIcon(newHeading))

  breadcrumbs.push(pos)
  if (breadcrumbs.length > 150) breadcrumbs.shift()
  flightPath.setLatLngs(breadcrumbs)

  map.panTo(pos, { animate: true, duration: 0.2 })
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.map-card {
  background: #09090b;
  border: 1px solid #27272a;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 330px;
  position: relative;
  margin-bottom: 0;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #040405;
  border-bottom: 1px solid #27272a;
  z-index: 1000;
}

.map-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.subsystem-code {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.65rem;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.1em;
}

.map-label {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #a1a1aa;
}

.coords-readout {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.7rem;
  color: #71717a;
  display: flex;
  gap: 6px;
}

.sep {
  color: #3f3f46;
}

.leaflet-viewport {
  flex: 1;
  width: 100%;
  background: #000000;
}
</style>

<style>
.vehicle-marker-div {
  background: transparent;
  border: none;
}
</style>