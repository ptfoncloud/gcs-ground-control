<template>
  <div class="pfd-container">
    <div class="pfd-topbar">
      <span class="pfd-tag">PFD-01</span>
      <span class="pfd-title">ATTITUDE DIRECTOR</span>
      <span class="pfd-rate">20 HZ</span>
    </div>

    <div class="svg-wrapper">
      <svg viewBox="0 0 240 240" class="adi-svg">
        <defs>
          <clipPath id="adi-viewport">
            <circle cx="120" cy="120" r="104" />
          </clipPath>
        </defs>

        <circle cx="120" cy="120" r="114" class="bezel-outer" />
        <circle cx="120" cy="120" r="106" class="bezel-inner" />

        <g clip-path="url(#adi-viewport)">
          <g :transform="`rotate(${-rollDeg}, 120, 120) translate(0, ${pitchTranslation})`">
            <rect x="-100" y="-400" width="440" height="520" class="sky-fill" />
            <rect x="-100" y="120" width="440" height="520" class="ground-fill" />
            <line x1="-100" y1="120" x2="340" y2="120" class="horizon-line" />

            <g class="pitch-rung climb">
              <path d="M 85 45 L 90 45 L 90 52 M 155 45 L 150 45 L 150 52" />
              <text x="76" y="48">30</text>
              <text x="159" y="48">30</text>
            </g>
            <g class="pitch-rung climb">
              <path d="M 80 70 L 95 70 L 95 77 M 160 70 L 145 70 L 145 77" />
              <text x="71" y="73">20</text>
              <text x="164" y="73">20</text>
            </g>
            <g class="pitch-rung climb">
              <path d="M 90 95 L 100 95 L 100 101 M 150 95 L 140 95 L 140 101" />
              <text x="81" y="98">10</text>
              <text x="154" y="98">10</text>
            </g>

            <g class="pitch-rung dive">
              <path d="M 90 145 L 100 145 L 100 139 M 150 145 L 140 145 L 140 139" stroke-dasharray="3,2" />
              <text x="81" y="148">-10</text>
              <text x="154" y="148">-10</text>
            </g>
            <g class="pitch-rung dive">
              <path d="M 80 170 L 95 170 L 95 163 M 160 170 L 145 170 L 145 163" stroke-dasharray="4,2" />
              <text x="71" y="173">-20</text>
              <text x="164" y="173">-20</text>
            </g>
            <g class="pitch-rung dive">
              <path d="M 85 195 L 90 195 L 90 188 M 155 195 L 150 195 L 150 188" stroke-dasharray="3,2" />
              <text x="76" y="198">-30</text>
              <text x="159" y="198">-30</text>
            </g>
          </g>
        </g>

        <g class="roll-scale">
          <polygon points="120,18 116,25 124,25" class="roll-zero-marker" />
          <line x1="120" y1="16" x2="120" y2="24" class="tick major" />
          <line x1="102" y1="18" x2="104" y2="24" class="tick" />
          <line x1="85" y1="23" x2="88" y2="29" class="tick" />
          <line x1="69" y1="33" x2="73" y2="38" class="tick major" />
          <line x1="50" y1="50" x2="55" y2="54" class="tick" />
          <line x1="138" y1="18" x2="136" y2="24" class="tick" />
          <line x1="155" y1="23" x2="152" y2="29" class="tick" />
          <line x1="171" y1="33" x2="167" y2="38" class="tick major" />
          <line x1="190" y1="50" x2="185" y2="54" class="tick" />
        </g>

        <polygon
          points="120,27 115,36 125,36"
          class="roll-sky-pointer"
          :transform="`rotate(${-rollDeg}, 120, 120)`"
        />

        <g class="aircraft-boresight">
          <circle cx="120" cy="120" r="3" class="boresight-pip" />
          <path d="M 75 120 L 102 120 L 102 127" class="boresight-wing" />
          <path d="M 165 120 L 138 120 L 138 127" class="boresight-wing" />
        </g>

        <circle cx="120" cy="120" r="104" class="glass-rim" />
      </svg>
    </div>

    <div class="pfd-readouts">
      <div class="readout-col">
        <span class="readout-lbl">PITCH</span>
        <span class="readout-val">{{ pitchDeg >= 0 ? '+' : '' }}{{ pitchDeg.toFixed(1) }}°</span>
      </div>
      <div class="readout-divider"></div>
      <div class="readout-col">
        <span class="readout-lbl">ROLL</span>
        <span class="readout-val">{{ rollDeg >= 0 ? '+' : '' }}{{ rollDeg.toFixed(1) }}°</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  pitchRad: {
    type: Number,
    default: 0
  },
  rollRad: {
    type: Number,
    default: 0
  }
})

const pitchDeg = computed(() => (props.pitchRad * 180) / Math.PI)
const rollDeg = computed(() => (props.rollRad * 180) / Math.PI)

const pitchTranslation = computed(() => {
  const px = pitchDeg.value * 2.5
  return Math.max(-95, Math.min(95, px))
})
</script>

<style scoped>
.pfd-container {
  background: #09090b;
  border: 1px solid #27272a;
  border-top: 3px solid #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14px 16px;
  box-sizing: border-box;
}

.pfd-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 10px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.pfd-tag {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.15em;
  color: #71717a;
}

.pfd-title {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.15em;
  color: #ffffff;
}

.pfd-rate {
  font-size: 0.65rem;
  font-family: "Consolas", "SF Mono", monospace;
  font-weight: 700;
  color: #22c55e;
}

.svg-wrapper {
  width: 220px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.adi-svg {
  width: 100%;
  height: 100%;
  user-select: none;
  overflow: visible;
}

.bezel-outer {
  fill: #000000;
  stroke: #27272a;
  stroke-width: 2;
}

.bezel-inner {
  fill: #09090b;
  stroke: #3f3f46;
  stroke-width: 1;
}

.glass-rim {
  fill: none;
  stroke: #27272a;
  stroke-width: 2;
}

.sky-fill {
  fill: #18181b;
}

.ground-fill {
  fill: #000000;
}

.horizon-line {
  stroke: #ffffff;
  stroke-width: 2;
}

.pitch-rung path {
  fill: none;
  stroke: #ffffff;
  stroke-width: 1.5;
}

.pitch-rung text {
  fill: #a1a1aa;
  font-size: 8px;
  font-family: "Consolas", "SF Mono", monospace;
  font-weight: 700;
  text-anchor: middle;
}

.roll-scale .tick {
  stroke: #71717a;
  stroke-width: 1.5;
}

.roll-scale .tick.major {
  stroke: #ffffff;
  stroke-width: 2;
}

.roll-zero-marker {
  fill: #ffffff;
}

.roll-sky-pointer {
  fill: #eab308;
}

.aircraft-boresight .boresight-pip {
  fill: #ffffff;
}

.aircraft-boresight .boresight-wing {
  fill: none;
  stroke: #ffffff;
  stroke-width: 3;
  stroke-linecap: square;
}

.pfd-readouts {
  display: flex;
  align-items: center;
  justify-content: space-around;
  width: 100%;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #18181b;
}

.readout-col {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.readout-lbl {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #71717a;
}

.readout-val {
  font-family: "Consolas", "SF Mono", monospace;
  font-size: 0.95rem;
  font-weight: 800;
  color: #ffffff;
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}

.readout-divider {
  width: 1px;
  height: 24px;
  background: #27272a;
}
</style>
