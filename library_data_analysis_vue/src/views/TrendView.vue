<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { readerApi } from '@/api/readers'
import { borrowApi } from '@/api/borrows'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(true)
const activeTab = ref('monthly')
const monthlyTrend = ref([])
const dailyTrend = ref([])

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const fetchTrendData = async () => {
  loading.value = true
  try {
    const [readerData, dailyRes] = await Promise.all([
      readerApi.getAll(),
      borrowApi.getDailyTrend()
    ])
    if (readerData.monthlyTrend) monthlyTrend.value = readerData.monthlyTrend
    if (dailyRes.ok) dailyTrend.value = await dailyRes.json()
  } catch (e) {
    console.error('Failed to fetch trend data', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.allData, (data) => {
  if (data) {
    if (data.readers?.monthlyTrend) monthlyTrend.value = data.readers.monthlyTrend
    loading.value = false
  }
}, { immediate: true, deep: true })

onMounted(async () => {
  if (!props.allData?.readers?.monthlyTrend) {
    await fetchTrendData()
  } else {
    try {
      const dailyRes = await borrowApi.getDailyTrend()
      if (dailyRes.ok) dailyTrend.value = await dailyRes.json()
    } catch (e) {
      console.error('Failed to fetch daily trend data', e)
    }
    loading.value = false
  }
})

const maxMonthly = computed(() => {
  if (!monthlyTrend.value.length) return 1
  return Math.max(...monthlyTrend.value.map(m => m.activeCount || m.count || 0))
})

const maxDaily = computed(() => {
  if (!dailyTrend.value.length) return 1
  return Math.max(...dailyTrend.value.map(d => d.count || 0))
})

const chartWidth = 800
const chartHeight = 300
const padding = 50

const monthlyChartPaths = computed(() => {
  const data = monthlyTrend.value
  if (!data.length) return { linePath: '', areaPath: '', points: [], maPath: '', trendPath: '' }

  const chartW = chartWidth - padding * 2
  const chartH = chartHeight - padding * 2
  const maxVal = maxMonthly.value
  const range = maxVal || 1

  const points = data.map((d, i) => ({
    x: padding + (i / (data.length - 1 || 1)) * chartW,
    y: padding + chartH - ((d.activeCount || d.count || 0) / range) * chartH,
    label: d.month,
    value: d.activeCount || d.count || 0
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = linePath +
    ` L ${points[points.length - 1].x} ${padding + chartH}` +
    ` L ${points[0].x} ${padding + chartH} Z`

  const windowSize = 3
  const maPoints = data.map((d, i) => {
    if (i < windowSize - 1) return null
    let sum = 0
    for (let j = i - windowSize + 1; j <= i; j++) {
      sum += (data[j].activeCount || data[j].count || 0)
    }
    const avg = sum / windowSize
    return {
      x: padding + (i / (data.length - 1 || 1)) * chartW,
      y: padding + chartH - (avg / range) * chartH
    }
  }).filter(Boolean)
  const maPath = maPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  const n = data.length
  const values = data.map(d => d.activeCount || d.count || 0)
  const xMean = (n + 1) / 2
  const yMean = values.reduce((s, v) => s + v, 0) / n
  let num = 0, den = 0
  for (let i = 0; i < n; i++) {
    num += (i + 1 - xMean) * (values[i] - yMean)
    den += (i + 1 - xMean) ** 2
  }
  const slope = den !== 0 ? num / den : 0
  const intercept = yMean - slope * xMean
  const clampY = (y) => Math.max(padding, Math.min(padding + chartH, y))
  const trendStart = { x: points[0].x, y: clampY(padding + chartH - ((slope * 1 + intercept) / range) * chartH) }
  const trendEnd = { x: points[n - 1].x, y: clampY(padding + chartH - ((slope * n + intercept) / range) * chartH) }
  const trendPath = `M ${trendStart.x} ${trendStart.y} L ${trendEnd.x} ${trendEnd.y}`

  return { linePath, areaPath, points, maPath, trendPath }
})

const dailyChartPaths = computed(() => {
  const data = dailyTrend.value
  if (!data.length) return { linePath: '', areaPath: '', points: [] }

  const chartW = chartWidth - padding * 2
  const chartH = chartHeight - padding * 2
  const maxVal = maxDaily.value
  const range = maxVal || 1

  const points = data.map((d, i) => ({
    x: padding + (i / (data.length - 1 || 1)) * chartW,
    y: padding + chartH - ((d.count || 0) / range) * chartH,
    label: d.date || '',
    value: d.count || 0
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = linePath +
    ` L ${points[points.length - 1].x} ${padding + chartH}` +
    ` L ${points[0].x} ${padding + chartH} Z`

  return { linePath, areaPath, points }
})

const hoveredPoint = ref(null)

const statCards = computed(() => {
  const data = monthlyTrend.value
  const total = data.reduce((s, d) => s + (d.activeCount || d.count || 0), 0)
  const avg = data.length ? Math.round(total / data.length) : 0
  const max = data.length ? Math.max(...data.map(d => d.activeCount || d.count || 0)) : 0
  const maxMonth = data.find(d => (d.activeCount || d.count) === max)?.month || '-'
  return [
    { i18nKey: 'trend.yearlyTotal', value: formatNumber(total), icon: 'total', color: '#d97706' },
    { i18nKey: 'trend.monthlyAvg', value: formatNumber(avg), icon: 'avg', color: '#3b82f6' },
    { i18nKey: 'trend.peakMonth', value: maxMonth, icon: 'peak', color: '#10b981' },
    { i18nKey: 'trend.peakValue', value: formatNumber(max), icon: 'max', color: '#f59e0b' }
  ]
})
</script>

<template>
  <div class="trend-view">
    <div class="page-header">
      <div class="header-info">
        <h1>{{ t('trend.title') }}</h1>
        <p>{{ t('trend.desc') }}</p>
      </div>
      <button class="refresh-btn btn btn-secondary btn-sm" @click="fetchTrendData" :disabled="loading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6"/>
          <path d="M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        <span>{{ t('common.refresh') }}</span>
      </button>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>{{ t('common.loading') }}</span>
    </div>

    <template v-else>
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.i18nKey" class="stat-card" :style="{ '--accent': card.color }">
          <div class="stat-icon">
            <svg v-if="card.icon === 'total'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <svg v-else-if="card.icon === 'avg'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="20" x2="12" y2="10"/>
              <line x1="18" y1="20" x2="18" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="16"/>
            </svg>
            <svg v-else-if="card.icon === 'peak'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3v18h18"/>
              <path d="M18 17V9"/>
              <path d="M13 17V5"/>
              <path d="M8 17v-3"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ t(card.i18nKey) }}</span>
            <span class="stat-value">{{ card.value }}</span>
          </div>
        </div>
      </div>

      <div class="tab-bar">
        <button class="tab-btn btn-tab" :class="{ active: activeTab === 'monthly' }" @click="activeTab = 'monthly'">{{ t('trend.monthlyTab') }}</button>
        <button class="tab-btn btn-tab" :class="{ active: activeTab === 'daily' }" @click="activeTab = 'daily'">{{ t('trend.dailyTab') }}</button>
      </div>

      <div v-if="activeTab === 'monthly'" class="card">
        <div class="card-header">
          <h3>{{ t('trend.monthlyActiveTrend') }}</h3>
          <span class="card-subtitle">{{ t('trend.monthlyActiveSubtitle') }}</span>
        </div>
        <div v-if="monthlyTrend.length" class="chart-container">
          <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="trend-chart">
            <defs>
              <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#d97706" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#d97706" stop-opacity="0.02"/>
              </linearGradient>
            </defs>
            <g class="grid-lines">
              <line v-for="i in 5" :key="'grid-' + i"
                :x1="padding" :y1="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                :x2="chartWidth - padding" :y2="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4"
              />
            </g>
            <path :d="monthlyChartPaths.areaPath" fill="url(#areaGrad)" />
            <path :d="monthlyChartPaths.linePath" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
            <path v-if="monthlyChartPaths.maPath" :d="monthlyChartPaths.maPath" fill="none" stroke="#f59e0b" stroke-width="2" stroke-dasharray="8 4" stroke-linecap="round" stroke-linejoin="round" />
            <path v-if="monthlyChartPaths.trendPath" :d="monthlyChartPaths.trendPath" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round" />
            <g v-for="(pt, idx) in monthlyChartPaths.points" :key="'pt-' + idx">
              <circle :cx="pt.x" :cy="pt.y" r="5" fill="white" stroke="#d97706" stroke-width="2"
                class="chart-point" :class="{ hovered: hoveredPoint === idx }"
                @mouseenter="hoveredPoint = idx" @mouseleave="hoveredPoint = null"
              />
              <g v-if="hoveredPoint === idx" class="tooltip">
                <template v-if="pt.y - 40 >= 0">
                  <rect :x="pt.x - 40" :y="pt.y - 40" width="80" height="30" rx="6" fill="#1e293b" />
                  <text :x="pt.x" :y="pt.y - 22" text-anchor="middle" font-size="12" fill="white" font-weight="600">
                    {{ formatNumber(pt.value) }}
                  </text>
                </template>
                <template v-else>
                  <rect :x="pt.x - 40" :y="pt.y + 10" width="80" height="30" rx="6" fill="#1e293b" />
                  <text :x="pt.x" :y="pt.y + 28" text-anchor="middle" font-size="12" fill="white" font-weight="600">
                    {{ formatNumber(pt.value) }}
                  </text>
                </template>
              </g>
              <text :x="pt.x" :y="chartHeight - 5" text-anchor="middle" font-size="12" fill="#64748b" font-weight="500" :transform="'rotate(-30,' + pt.x + ',' + (chartHeight - 5) + ')'">
                {{ pt.label }}
              </text>
            </g>
            <g transform="translate(60, 15)" class="chart-legend">
              <line x1="0" y1="0" x2="20" y2="0" stroke="#d97706" stroke-width="2.5" />
              <text x="25" y="4" font-size="11" fill="#64748b">{{ t('trend.rawData') }}</text>
              <line x1="100" y1="0" x2="120" y2="0" stroke="#f59e0b" stroke-width="2" stroke-dasharray="8 4" />
              <text x="125" y="4" font-size="11" fill="#64748b">{{ t('trend.movingAvg') }}</text>
              <line x1="220" y1="0" x2="240" y2="0" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 4" />
              <text x="245" y="4" font-size="11" fill="#64748b">{{ t('trend.trendLine') }}</text>
            </g>
          </svg>
        </div>
        <div v-else class="empty-chart">
          <svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" width="48" height="48">
            <path d="M3 3v18h18"/>
            <path d="M18 17V9"/>
            <path d="M13 17V5"/>
            <path d="M8 17v-3"/>
          </svg>
          <p>{{ t('common.noData') }}</p>
        </div>
      </div>

      <div v-if="activeTab === 'daily'" class="card">
        <div class="card-header">
          <h3>{{ t('trend.dailyBorrowTrend') }}</h3>
          <span class="card-subtitle">{{ t('trend.dailyBorrowSubtitle') }}</span>
        </div>
        <div v-if="dailyTrend.length" class="chart-container">
          <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="trend-chart">
            <defs>
              <linearGradient id="dailyAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.02"/>
              </linearGradient>
            </defs>
            <g class="grid-lines">
              <line v-for="i in 5" :key="'dgrid-' + i"
                :x1="padding" :y1="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                :x2="chartWidth - padding" :y2="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4"
              />
            </g>
            <path :d="dailyChartPaths.areaPath" fill="url(#dailyAreaGrad)" />
            <path :d="dailyChartPaths.linePath" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <g v-for="(pt, idx) in dailyChartPaths.points" :key="'dpt-' + idx">
              <circle v-if="idx % Math.ceil(dailyTrend.length / 30) === 0"
                :cx="pt.x" :cy="pt.y" r="3" fill="white" stroke="#06b6d4" stroke-width="2"
                class="chart-point" :class="{ hovered: hoveredPoint === idx }"
                @mouseenter="hoveredPoint = idx" @mouseleave="hoveredPoint = null"
              />
              <g v-if="hoveredPoint === idx" class="tooltip">
                <rect :x="pt.x - 50" :y="pt.y - 40" width="100" height="30" rx="6" fill="#1e293b" />
                <text :x="pt.x" :y="pt.y - 22" text-anchor="middle" font-size="11" fill="white" font-weight="600">
                  {{ pt.label }}: {{ formatNumber(pt.value) }}
                </text>
              </g>
              <text v-if="idx % Math.ceil(dailyTrend.length / 12) === 0"
                :x="pt.x" :y="chartHeight - 5" text-anchor="middle" font-size="12" fill="#64748b" font-weight="500" :transform="'rotate(-30,' + pt.x + ',' + (chartHeight - 5) + ')'">
                {{ pt.label.slice(4) }}
              </text>
            </g>
          </svg>
        </div>
        <div v-else class="empty-chart">
          <svg viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" width="48" height="48">
            <path d="M3 3v18h18"/>
            <path d="M18 17V9"/>
            <path d="M13 17V5"/>
            <path d="M8 17v-3"/>
          </svg>
          <p>{{ t('common.noData') }}</p>
        </div>
      </div>

      <div v-if="activeTab === 'monthly'" class="card">
        <div class="card-header">
          <h3>{{ t('trend.monthlyDetail') }}</h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('trend.month') }}</th>
              <th>{{ t('trend.activeCount') }}</th>
              <th>{{ t('trend.change') }}</th>
              <th>{{ t('trend.percent') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in monthlyTrend" :key="item.month">
              <td class="name-cell">{{ item.month }}</td>
              <td class="count-cell">{{ formatNumber(item.activeCount || item.count) }}</td>
              <td>
                <span v-if="idx > 0 && (monthlyTrend[idx-1]?.activeCount || monthlyTrend[idx-1]?.count || 0) > 0" class="change-tag" :class="(item.activeCount || item.count) >= (monthlyTrend[idx-1].activeCount || monthlyTrend[idx-1].count || 0) ? 'up' : 'down'">
                  {{ (item.activeCount || item.count) >= (monthlyTrend[idx-1]?.activeCount || monthlyTrend[idx-1]?.count || 0) ? '↑' : '↓' }}
                  {{ idx > 0 ? Math.abs((((item.activeCount || item.count || 0) - (monthlyTrend[idx-1]?.activeCount || monthlyTrend[idx-1]?.count || 0)) / (monthlyTrend[idx-1]?.activeCount || monthlyTrend[idx-1]?.count || 1) * 100)).toFixed(1) : 0 }}%
                </span>
                <span v-else class="change-tag neutral">-</span>
              </td>
              <td>
                <div class="percent-bar">
                  <div class="percent-fill" :style="{ width: ((item.activeCount || item.count || 0) / maxMonthly * 100) + '%' }"></div>
                  <span class="percent-text">{{ ((item.activeCount || item.count || 0) / (monthlyTrend.reduce((s, d) => s + (d.activeCount || d.count || 0), 0) || 1) * 100).toFixed(1) }}%</span>
                </div>
              </td>
            </tr>
            <tr v-if="monthlyTrend.length === 0" class="empty-row">
              <td colspan="4">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.trend-view {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 14px;
  color: var(--color-neutral-500);
  margin: 0;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: #94a3b8;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-neutral-0);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--color-neutral-200);
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--accent) 10%, var(--color-neutral-0));
  color: var(--accent);
  flex-shrink: 0;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 10px;
}

.tab-btn {
  flex: 1;
}

.card {
  background: var(--color-neutral-0);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid var(--color-neutral-200);
  margin-bottom: 16px;
}

.card-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.card-subtitle {
  font-size: 13px;
  color: #94a3b8;
}

.chart-container {
  width: 100%;
  overflow-x: auto;
}

.trend-chart {
  width: 100%;
  min-width: 600px;
}

.chart-point {
  cursor: pointer;
  transition: all 0.15s;
}

.chart-point.hovered {
  r: 7;
  fill: var(--color-primary-500);
}

.empty-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-chart p {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-neutral-500);
  margin: 16px 0 4px;
}

.empty-chart span {
  font-size: 13px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  border-bottom: 2px solid var(--color-neutral-200);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--color-neutral-600);
  border-bottom: 1px solid #f1f5f9;
}

.data-table tbody tr:hover td {
  background: var(--color-neutral-50);
}

.name-cell {
  font-weight: 600;
  color: #1e293b;
}

.count-cell {
  font-weight: 600;
  color: var(--color-primary-500);
}

.change-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.change-tag.up {
  color: #10b981;
  background: #ecfdf5;
}

.change-tag.down {
  color: #ef4444;
  background: #fef2f2;
}

.change-tag.neutral {
  color: #94a3b8;
  background: #f1f5f9;
}

.percent-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.percent-fill {
  height: 6px;
  background: linear-gradient(90deg, var(--color-primary-500), #fbbf24);
  border-radius: 3px;
  min-width: 4px;
  flex: 1;
  max-width: 120px;
  transition: width 0.5s ease;
}

.percent-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary-500);
  min-width: 45px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.empty-row td {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
}
</style>
