<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  colors: {
    type: Array,
    default: () => ['#1677ff', '#52c41a', '#faad14', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16']
  },
  size: { type: Number, default: 180 }
})

const total = computed(() => props.data.reduce((s, d) => s + (d.value || 0), 0))

const pieData = computed(() => {
  let startAngle = -90
  return props.data.map((item, idx) => {
    const angle = total.value > 0 ? (item.value / total.value) * 360 : 0
    const endAngle = startAngle + angle
    const rad = (startAngle + angle / 2) * Math.PI / 180
    const cx = props.size / 2
    const cy = props.size / 2
    const r = props.size / 2 - 10
    const x1 = cx + r * Math.cos(rad - Math.PI / 2)
    const y1 = cy + r * Math.sin(rad - Math.PI / 2)
    const x2 = cx + r * Math.cos(rad + angle * Math.PI / 180 - Math.PI / 2)
    const y2 = cy + r * Math.sin(rad + angle * Math.PI / 180 - Math.PI / 2)
    const large = angle > 180 ? 1 : 0
    const path = angle > 0 
      ? `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`
      : ''
    startAngle = endAngle
    return {
      ...item,
      path,
      color: item.color || props.colors[idx % props.colors.length]
    }
  }).filter(d => d.path)
})
</script>

<template>
  <div class="pie-chart">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" class="pie-svg">
      <g v-for="(item, idx) in pieData" :key="idx">
        <path
          :d="item.path"
          :fill="item.color"
          class="pie-slice"
        />
      </g>
      <text :x="size / 2" :y="size / 2 - 8" text-anchor="middle" class="pie-total">{{ total.toLocaleString() }}</text>
      <text :x="size / 2" :y="size / 2 + 12" text-anchor="middle" class="pie-label">总计</text>
    </svg>
    <div class="pie-legend">
      <div v-for="(item, idx) in data" :key="idx" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color || colors[idx % colors.length] }"></span>
        <span class="legend-name">{{ item.name }}</span>
        <span class="legend-value">{{ item.value?.toLocaleString() }}</span>
        <span class="legend-percent">{{ item.percent || 0 }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pie-chart {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 16px;
}

.pie-svg {
  flex-shrink: 0;
}

.pie-slice {
  transition: opacity 0.2s;
}

.pie-slice:hover {
  opacity: 0.8;
}

.pie-total {
  font-size: 24px;
  font-weight: 700;
  fill: #1f2937;
}

.pie-label {
  font-size: 12px;
  fill: #6b7280;
}

.pie-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  color: #374151;
}

.legend-value {
  font-weight: 600;
  color: #1f2937;
  min-width: 60px;
  text-align: right;
}

.legend-percent {
  color: #9ca3af;
  min-width: 45px;
  text-align: right;
}
</style>
