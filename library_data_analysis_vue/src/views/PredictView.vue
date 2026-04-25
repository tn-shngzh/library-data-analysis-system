<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(false)
const activeModel = ref('moving_avg')
const predictionMonths = ref(3)
const showPrediction = ref(false)
const predictionResult = ref(null)

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const monthlyTrend = computed(() => props.allData?.readers?.monthlyTrend || [])

const statCards = computed(() => {
  const data = monthlyTrend.value
  const total = data.reduce((s, d) => s + (d.count || 0), 0)
  const avg = data.length ? Math.round(total / data.length) : 0
  return [
    { i18nKey: 'predict.historicalData', value: data.length + ' ' + t('predict.months'), icon: 'database', color: '#6366f1' },
    { i18nKey: 'predict.monthlyAvg', value: formatNumber(avg), icon: 'avg', color: '#3b82f6' },
    { i18nKey: 'predict.predictionModel', value: activeModel.value === 'moving_avg' ? t('predict.movingAvg') : t('predict.linearRegression'), icon: 'model', color: '#10b981' },
    { i18nKey: 'predict.predictionPeriod', value: predictionMonths.value + ' ' + t('predict.months'), icon: 'calendar', color: '#f59e0b' }
  ]
})

const generatePrediction = () => {
  const data = monthlyTrend.value
  if (data.length < 3) return

  showPrediction.value = true
  const counts = data.map(d => d.count || 0)

  let predictions = []
  if (activeModel.value === 'moving_avg') {
    const windowSize = 3
    const lastValues = counts.slice(-windowSize)
    const avg = lastValues.reduce((s, v) => s + v, 0) / windowSize
    const trend = counts.length >= 6
      ? (counts.slice(-3).reduce((s, v) => s + v, 0) - counts.slice(-6, -3).reduce((s, v) => s + v, 0)) / 3
      : 0

    for (let i = 1; i <= predictionMonths.value; i++) {
      const predicted = Math.max(0, Math.round(avg + trend * i * 0.3))
      const confidence = Math.max(60, 95 - i * 10)
      predictions.push({
        month: `${12 + i}${t('predict.month')}`,
        predicted,
        lower: Math.max(0, Math.round(predicted * (1 - (100 - confidence) / 100))),
        upper: Math.round(predicted * (1 + (100 - confidence) / 100)),
        confidence
      })
    }
  } else {
    const n = counts.length
    const xMean = (n + 1) / 2
    const yMean = counts.reduce((s, v) => s + v, 0) / n
    let num = 0, den = 0
    for (let i = 0; i < n; i++) {
      num += (i + 1 - xMean) * (counts[i] - yMean)
      den += (i + 1 - xMean) ** 2
    }
    const slope = den !== 0 ? num / den : 0
    const intercept = yMean - slope * xMean

    for (let i = 1; i <= predictionMonths.value; i++) {
      const x = n + i
      const predicted = Math.max(0, Math.round(slope * x + intercept))
      const confidence = Math.max(55, 92 - i * 12)
      predictions.push({
        month: `${12 + i}${t('predict.month')}`,
        predicted,
        lower: Math.max(0, Math.round(predicted * (1 - (100 - confidence) / 100))),
        upper: Math.round(predicted * (1 + (100 - confidence) / 100)),
        confidence
      })
    }
  }

  predictionResult.value = predictions
}

const chartWidth = 800
const chartHeight = 300
const padding = 50

const combinedChartPaths = computed(() => {
  const data = monthlyTrend.value
  const pred = predictionResult.value || []
  if (!data.length) return { linePath: '', areaPath: '', predPath: '', points: [], predPoints: [] }

  const allValues = [
    ...data.map(d => d.count || 0),
    ...pred.map(p => p.upper || 0)
  ]
  const maxVal = Math.max(...allValues) || 1
  const totalPoints = data.length + pred.length
  const chartW = chartWidth - padding * 2
  const chartH = chartHeight - padding * 2

  const points = data.map((d, i) => ({
    x: padding + (i / (totalPoints - 1 || 1)) * chartW,
    y: padding + chartH - ((d.count || 0) / maxVal) * chartH,
    label: d.month,
    value: d.count || 0,
    type: 'actual'
  }))

  const lastActual = points[points.length - 1]
  const predPoints = pred.map((p, i) => ({
    x: padding + ((data.length + i) / (totalPoints - 1 || 1)) * chartW,
    y: padding + chartH - (p.predicted / maxVal) * chartH,
    label: p.month,
    value: p.predicted,
    upper: padding + chartH - (p.upper / maxVal) * chartH,
    lower: padding + chartH - (p.lower / maxVal) * chartH,
    type: 'predicted'
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const areaPath = linePath +
    ` L ${points[points.length - 1].x} ${padding + chartH}` +
    ` L ${points[0].x} ${padding + chartH} Z`

  let predPath = ''
  if (predPoints.length && lastActual) {
    predPath = `M ${lastActual.x} ${lastActual.y} ` +
      predPoints.map(p => `L ${p.x} ${p.y}`).join(' ')
  }

  return { linePath, areaPath, predPath, points, predPoints, maxVal }
})

watch(() => props.allData, (data) => {
  if (data) {
    loading.value = false
  }
}, { immediate: true, deep: true })

onMounted(() => {
  if (props.allData) {
    loading.value = false
  }
})
</script>

<template>
  <div class="predict-view">
    <div class="page-header">
      <div class="header-info">
        <h1>{{ t('predict.title') }}</h1>
        <p>{{ t('predict.desc') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>{{ t('common.loading') }}</span>
    </div>

    <template v-else>
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.i18nKey" class="stat-card" :style="{ '--accent': card.color }">
          <div class="stat-icon">
            <svg v-if="card.icon === 'database'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
            </svg>
            <svg v-else-if="card.icon === 'avg'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="20" x2="12" y2="10"/>
              <line x1="18" y1="20" x2="18" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="16"/>
            </svg>
            <svg v-else-if="card.icon === 'model'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ t(card.i18nKey) }}</span>
            <span class="stat-value">{{ card.value }}</span>
          </div>
        </div>
      </div>

      <div class="config-card">
        <div class="card-header">
          <h3>{{ t('predict.config') }}</h3>
        </div>
        <div class="config-form">
          <div class="form-group">
            <label>{{ t('predict.predictionModel') }}</label>
            <div class="model-options">
              <button
                class="model-btn"
                :class="{ active: activeModel === 'moving_avg' }"
                @click="activeModel = 'moving_avg'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
                <span>{{ t('predict.movingAvg') }}</span>
                <small>{{ t('predict.movingAvgDesc') }}</small>
              </button>
              <button
                class="model-btn"
                :class="{ active: activeModel === 'linear' }"
                @click="activeModel = 'linear'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="19" x2="19" y2="5"/>
                </svg>
                <span>{{ t('predict.linearRegression') }}</span>
                <small>{{ t('predict.linearRegressionDesc') }}</small>
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>{{ t('predict.predictionPeriod') }}</label>
            <div class="month-selector">
              <button
                v-for="m in [1, 2, 3, 6]"
                :key="m"
                class="month-btn"
                :class="{ active: predictionMonths === m }"
                @click="predictionMonths = m"
              >{{ m }}{{ t('predict.monthsShort') }}</button>
            </div>
          </div>
          <button class="predict-btn" @click="generatePrediction" :disabled="monthlyTrend.length < 3">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13"/>
              <path d="M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
            <span>{{ t('predict.startPrediction') }}</span>
          </button>
        </div>
      </div>

      <div v-if="monthlyTrend.length < 3" class="card warning-card">
        <div class="warning-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <div>
            <h4>{{ t('predict.insufficientData') }}</h4>
            <p>{{ t('predict.insufficientDataDesc') }}</p>
          </div>
        </div>
      </div>

      <div v-if="showPrediction && predictionResult" class="card">
        <div class="card-header">
          <h3>{{ t('predict.result') }}</h3>
          <span class="card-subtitle">{{ activeModel === 'moving_avg' ? t('predict.movingAvgModel') : t('predict.linearRegressionModel') }}</span>
        </div>
        <div class="chart-container">
          <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="predict-chart">
            <defs>
              <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#6366f1" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0.02"/>
              </linearGradient>
            </defs>
            <g class="grid-lines">
              <line v-for="i in 5" :key="'grid-' + i"
                :x1="padding" :y1="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                :x2="chartWidth - padding" :y2="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4"
              />
            </g>
            <path :d="combinedChartPaths.areaPath" fill="url(#actualGrad)" />
            <path :d="combinedChartPaths.linePath" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
            <path v-if="combinedChartPaths.predPath" :d="combinedChartPaths.predPath" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="8 4" stroke-linecap="round" stroke-linejoin="round" />
            <g v-for="(pt, idx) in combinedChartPaths.points" :key="'actual-' + idx">
              <circle :cx="pt.x" :cy="pt.y" r="4" fill="#6366f1" />
              <text :x="pt.x" :y="chartHeight - 8" text-anchor="middle" font-size="10" fill="#94a3b8">{{ pt.label }}</text>
            </g>
            <g v-for="(pt, idx) in combinedChartPaths.predPoints" :key="'pred-' + idx">
              <circle :cx="pt.x" :cy="pt.y" r="5" fill="#f59e0b" stroke="white" stroke-width="2" />
              <line v-if="pt.upper && pt.lower" :x1="pt.x" :y1="pt.upper" :x2="pt.x" :y2="pt.lower" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
              <line v-if="pt.upper && pt.lower" :x1="pt.x - 4" :y1="pt.upper" :x2="pt.x + 4" :y2="pt.upper" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
              <line v-if="pt.upper && pt.lower" :x1="pt.x - 4" :y1="pt.lower" :x2="pt.x + 4" :y2="pt.lower" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
              <text :x="pt.x" :y="chartHeight - 8" text-anchor="middle" font-size="10" fill="#f59e0b" font-weight="600">{{ pt.label }}</text>
            </g>
          </svg>
        </div>

        <div class="legend-bar">
          <div class="legend-item">
            <span class="legend-dot actual"></span>
            <span>{{ t('predict.actualData') }}</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot predicted"></span>
            <span>{{ t('predict.predictedData') }}</span>
          </div>
          <div class="legend-item">
            <span class="legend-line confidence"></span>
            <span>{{ t('predict.confidenceInterval') }}</span>
          </div>
        </div>
      </div>

      <div v-if="showPrediction && predictionResult" class="card">
        <div class="card-header">
          <h3>{{ t('predict.predictionDetail') }}</h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('predict.month') }}</th>
              <th>{{ t('predict.predictedValue') }}</th>
              <th>{{ t('predict.lowerBound') }}</th>
              <th>{{ t('predict.upperBound') }}</th>
              <th>{{ t('predict.confidence') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in predictionResult" :key="item.month">
              <td class="name-cell">{{ item.month }}</td>
              <td class="count-cell">{{ formatNumber(item.predicted) }}</td>
              <td>{{ formatNumber(item.lower) }}</td>
              <td>{{ formatNumber(item.upper) }}</td>
              <td>
                <span class="confidence-tag" :class="{ high: item.confidence >= 80, medium: item.confidence >= 60 && item.confidence < 80, low: item.confidence < 60 }">
                  {{ item.confidence }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.predict-view {
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
  color: #64748b;
  margin: 0;
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
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
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
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid #e2e8f0;
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
  background: color-mix(in srgb, var(--accent) 10%, white);
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

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e2e8f0;
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

.config-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 10px;
}

.model-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.model-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 16px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.model-btn:hover {
  border-color: #a5b4fc;
  background: #eef2ff;
}

.model-btn.active {
  border-color: #6366f1;
  background: #eef2ff;
  box-shadow: 0 0 0 1px #6366f1;
}

.model-btn svg {
  width: 24px;
  height: 24px;
  color: #6366f1;
  margin-bottom: 4px;
}

.model-btn span {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.model-btn small {
  font-size: 12px;
  color: #94a3b8;
}

.month-selector {
  display: flex;
  gap: 8px;
}

.month-btn {
  padding: 8px 20px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.month-btn:hover {
  border-color: #a5b4fc;
}

.month-btn.active {
  border-color: #6366f1;
  background: #6366f1;
  color: white;
}

.predict-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 32px;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.predict-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.predict-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.predict-btn svg {
  width: 18px;
  height: 18px;
}

.warning-card {
  border-color: #fbbf24;
  background: #fffbeb;
}

.warning-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.warning-content svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.warning-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #92400e;
  margin: 0 0 2px;
}

.warning-content p {
  font-size: 13px;
  color: #a16207;
  margin: 0;
}

.chart-container {
  width: 100%;
  overflow-x: auto;
}

.predict-chart {
  width: 100%;
  min-width: 600px;
}

.legend-bar {
  display: flex;
  gap: 24px;
  padding: 16px 0 0;
  border-top: 1px solid #f1f5f9;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.actual {
  background: #6366f1;
}

.legend-dot.predicted {
  background: #f59e0b;
}

.legend-line {
  width: 20px;
  height: 2px;
  border-top: 2px dashed #f59e0b;
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
  border-bottom: 2px solid #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: #475569;
  border-bottom: 1px solid #f1f5f9;
}

.data-table tbody tr:hover td {
  background: #f8fafc;
}

.name-cell {
  font-weight: 600;
  color: #1e293b;
}

.count-cell {
  font-weight: 600;
  color: #f59e0b;
}

.confidence-tag {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 4px;
}

.confidence-tag.high {
  color: #10b981;
  background: #ecfdf5;
}

.confidence-tag.medium {
  color: #f59e0b;
  background: #fffbeb;
}

.confidence-tag.low {
  color: #ef4444;
  background: #fef2f2;
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

  .model-options {
    grid-template-columns: 1fr;
  }

  .month-selector {
    flex-wrap: wrap;
  }
}
</style>
