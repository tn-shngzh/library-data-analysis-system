<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  color: { type: String, default: '#1677ff' },
  chartType: { type: String, default: 'bar', validator: (v) => ['bar', 'line'].includes(v) }
})

const maxValue = computed(() => Math.max(...props.data.map(d => d.value || 0), 1))
const chartHeight = 200
const barWidth = computed(() => {
  const len = props.data.length
  if (len <= 7) return 40
  if (len <= 14) return 30
  return 20
})

const svgPath = computed(() => {
  const width = 800
  const height = 200
  const padding = 30
  const dataLen = props.data.length
  if (dataLen <= 1) return ''

  const points = props.data.map((d, i) => {
    const x = padding + (i / (dataLen - 1)) * (width - padding * 2)
    const y = height - padding - ((d.value || 0) / maxValue.value) * (height - padding * 2)
    return { x, y }
  })

  return points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
})

const svgArea = computed(() => {
  const width = 800
  const height = 200
  const padding = 30
  const dataLen = props.data.length
  if (dataLen <= 1) return ''

  const points = props.data.map((d, i) => {
    const x = padding + (i / (dataLen - 1)) * (width - padding * 2)
    const y = height - padding - ((d.value || 0) / maxValue.value) * (height - padding * 2)
    return { x, y }
  })

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const bottomY = height - padding
  const lastP = points[points.length - 1]
  const firstP = points[0]
  return `${linePath} L${lastP.x},${bottomY} L${firstP.x},${bottomY} Z`
})
</script>

<template>
  <div class="trend-chart">
    <div v-if="chartType === 'bar'" class="bar-chart">
      <div 
        v-for="(item, idx) in data" 
        :key="idx"
        class="bar-item"
      >
        <div class="bar-wrapper">
          <div 
            class="bar-fill"
            :style="{
              height: `${(item.value / maxValue) * 100}%`,
              backgroundColor: color
            }"
          >
            <span class="bar-value">{{ item.value }}</span>
          </div>
        </div>
        <span class="bar-label">{{ item.label }}</span>
      </div>
    </div>

    <div v-else class="line-chart">
      <svg class="line-svg" viewBox="0 0 800 200" preserveAspectRatio="none">
        <path :d="svgArea" :fill="color" fill-opacity="0.1" />
        <path :d="svgPath" :stroke="color" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        <circle
          v-for="(item, idx) in data"
          :key="idx"
          :cx="30 + (idx / (data.length - 1 || 1)) * 740"
          :cy="200 - 30 - ((item.value || 0) / maxValue) * 140"
          r="3"
          :fill="color"
        />
      </svg>
      <div class="line-labels">
        <span 
          v-for="(item, idx) in data" 
          :key="idx"
          class="line-label"
        >{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.trend-chart {
  width: 100%;
  height: 220px;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 200px;
  padding: 0 8px;
  gap: 4px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 60px;
  gap: 8px;
}

.bar-wrapper {
  width: 100%;
  height: 180px;
  display: flex;
  align-items: flex-end;
}

.bar-fill {
  width: 100%;
  min-height: 4px;
  border-radius: 6px 6px 0 0;
  transition: height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  display: flex;
  justify-content: center;
}

.bar-fill:hover {
  opacity: 0.85;
}

.bar-value {
  position: absolute;
  top: -24px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.bar-label {
  font-size: 10px;
  color: #94a3b8;
  text-align: center;
  max-width: 50px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line-chart {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
}

.line-svg {
  width: 100%;
  height: 170px;
}

.line-labels {
  display: flex;
  justify-content: space-around;
  padding: 0 30px;
}

.line-label {
  font-size: 10px;
  color: #94a3b8;
  text-align: center;
  max-width: 50px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
