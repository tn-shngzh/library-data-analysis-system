<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatNumber } from '@/utils/format'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'

const { t } = useI18n()

const props = defineProps({
  allData: { type: Object, default: null }
})

const loading = ref(false)
const selectedTarget = ref('borrowCount')
const selectedModel = ref('holtWinters')
const predictionPeriod = ref(3)
const showPrediction = ref(false)
const predictionResults = ref(null)

const predictionTargets = [
  { id: 'borrowCount', label: 'predict.borrowCount', color: '#d97706' },
  { id: 'returnCount', label: 'predict.returnCount', color: '#10b981' }
]

const predictionModels = [
  { id: 'arima', label: 'predict.arima' },
  { id: 'linearTrend', label: 'predict.linearRegression' },
  { id: 'movingAverage', label: 'predict.movingAvg' },
  { id: 'simpleES', label: 'predict.simpleES' },
  { id: 'holtLinear', label: 'predict.holtLinear' },
  { id: 'holtWinters', label: 'predict.holtWinters' }
]

function simpleExponentialSmoothing(data, alpha = 0.3) {
  let s = data[0]
  for (let i = 1; i < data.length; i++) s = alpha * data[i] + (1 - alpha) * s
  return s
}

function holtLinear(data, alpha = 0.3, beta = 0.1) {
  let level = data[0]
  let trend = data.length > 1 ? data[1] - data[0] : 0
  for (let i = 1; i < data.length; i++) {
    const prevLevel = level
    level = alpha * data[i] + (1 - alpha) * (level + trend)
    trend = beta * (level - prevLevel) + (1 - beta) * trend
  }
  return { level, trend }
}

function holtWinters(data, alpha = 0.3, beta = 0.1, gamma = 0.1, period = 12) {
  if (data.length < 2) return { level: data[data.length - 1], trend: 0, seasonal: Array(period).fill(1) }
  const n = data.length
  const seasonal = Array(period).fill(1)
  const seasonCounts = Array(period).fill(0)
  const avgPeriod = Math.min(period, Math.floor(n / 2)) || 1
  for (let i = 0; i < n; i++) { seasonal[i % avgPeriod] += data[i]; seasonCounts[i % avgPeriod]++ }
  for (let i = 0; i < avgPeriod; i++) { if (seasonCounts[i] > 0) seasonal[i] /= seasonCounts[i] }
  const avgSeasonal = seasonal.slice(0, avgPeriod).reduce((s, v) => s + v, 0) / avgPeriod
  for (let i = 0; i < avgPeriod; i++) seasonal[i] = seasonal[i] / avgSeasonal
  let level = data[0]
  let trend = 0
  if (n > 1) trend = (data[n - 1] - data[0]) / n
  for (let i = 1; i < n; i++) {
    const prevLevel = level
    level = alpha * (data[i] / seasonal[i % avgPeriod]) + (1 - alpha) * (level + trend)
    trend = beta * (level - prevLevel) + (1 - beta) * trend
  }
  return { level, trend, seasonal: seasonal.slice(0, avgPeriod), period: avgPeriod }
}

function linearRegression(data) {
  const n = data.length
  if (n < 2) return { slope: 0, intercept: data[0] || 0 }
  let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0
  for (let i = 0; i < n; i++) { sumX += i; sumY += data[i]; sumXY += i * data[i]; sumXX += i * i }
  const denom = n * sumXX - sumX * sumX
  if (Math.abs(denom) < 1e-10) return { slope: 0, intercept: sumY / n }
  return { slope: (n * sumXY - sumX * sumY) / denom, intercept: (sumY - ((n * sumXY - sumX * sumY) / denom) * sumX) / n }
}

function arima(data, p = 1, d = 1, q = 1) {
  const differenced = []
  for (let i = d; i < data.length; i++) differenced.push(data[i] - data[i - 1])
  let ar = 0, ma = 0
  if (differenced.length > p + q) {
    const n = differenced.length
    let sumAR = 0, sumMA = 0
    for (let i = p; i < n - q; i++) { sumAR += differenced[i] * differenced[i - p]; sumMA += differenced[i] * differenced[i - q] }
    ar = sumAR / (n - p - q) / 1000
    ma = sumMA / (n - p - q) / 1000
  }
  const avg = data.reduce((s, v) => s + v, 0) / data.length
  const trend = data.length > 1 ? (data[data.length - 1] - data[0]) / data.length : 0
  return { ar, ma, avg, trend, differenced }
}

function generatePredictions(model, data, periods) {
  const predictions = []
  switch (model) {
    case 'simpleES': {
      const smoothed = simpleExponentialSmoothing(data)
      for (let i = 1; i <= periods; i++) predictions.push(Math.max(0, smoothed))
      break
    }
    case 'holtLinear': {
      const { level, trend } = holtLinear(data)
      for (let i = 1; i <= periods; i++) predictions.push(Math.max(0, level + trend * i))
      break
    }
    case 'holtWinters': {
      const result = holtWinters(data)
      for (let i = 1; i <= periods; i++) {
        const seasonalFactor = result.seasonal[(data.length + i - 1) % result.period]
        predictions.push(Math.max(0, (result.level + result.trend * i) * seasonalFactor))
      }
      break
    }
    case 'arima': {
      const modelResult = arima(data)
      for (let i = 1; i <= periods; i++) {
        const seasonality = data.length > 1 ? data[data.length - i] / modelResult.avg : 1
        predictions.push(Math.max(0, (modelResult.avg + modelResult.trend * i) * seasonality))
      }
      break
    }
    case 'linearTrend': {
      const { slope, intercept } = linearRegression(data)
      for (let i = 1; i <= periods; i++) {
        const trendValue = slope * (data.length + i - 1) + intercept
        const avgSeasonal = data.length > 1 ? data[data.length - i] / (intercept + slope * (data.length - 1)) : 1
        predictions.push(Math.max(0, trendValue * avgSeasonal))
      }
      break
    }
    case 'movingAverage': {
      if (data.length < 3) {
        const avg = data.reduce((s, v) => s + v, 0) / data.length
        for (let i = 0; i < periods; i++) predictions.push(avg)
      } else {
        const window = Math.min(3, data.length)
        let sum = 0
        for (let i = data.length - window; i < data.length; i++) sum += data[i]
        const maBase = sum / window
        const residuals = []
        for (let i = window; i < data.length; i++) {
          const maPrev = data.slice(i - window, i).reduce((s, v) => s + v, 0) / window
          if (maPrev > 0) residuals.push((data[i] - maPrev) / maPrev)
        }
        const avgResidual = residuals.length > 0 ? residuals.reduce((s, v) => s + v, 0) / residuals.length : 0
        const lastMa = data.slice(-window).reduce((s, v) => s + v, 0) / window
        for (let i = 0; i < periods; i++) predictions.push(Math.max(0, lastMa * (1 + avgResidual * (i + 1) * 0.5)))
      }
      break
    }
  }
  return predictions
}

function computeConfidence(predictions, data) {
  const residuals = []
  for (let i = 1; i < data.length; i++) {
    if (data[i - 1] > 0) residuals.push(Math.abs(data[i] - data[i - 1]) / data[i - 1] * 100)
  }
  const avgError = residuals.length ? residuals.reduce((s, v) => s + v, 0) / residuals.length : 10
  return predictions.map((_, i) => ({
    lower: Math.round(Math.max(0, predictions[i] * (1 - avgError / 100 * (1 + i * 0.2)))),
    upper: Math.round(predictions[i] * (1 + avgError / 100 * (1 + i * 0.2))),
    confidence: Math.max(60, 95 - i * 8)
  }))
}

const historicalData = computed(() => {
  const data = props.allData
  if (!data) return []
  switch (selectedTarget.value) {
    case 'borrowCount': return data.borrows?.monthlyBorrows || data.overview?.stats?.monthlyBorrows || []
    case 'returnCount': return data.borrows?.monthlyReturns || data.overview?.stats?.monthlyReturns || []
    default: return []
  }
})

const historicalValues = computed(() => {
  return historicalData.value.map(d => {
    const val = d.count || d.value || 0
    return typeof val === 'number' && !isNaN(val) ? val : 0
  }).filter(v => v > 0)
})

const historicalLabels = computed(() => historicalData.value.map(d => d.month || d.label || ''))

const selectedTargetColor = computed(() => {
  return predictionTargets.find(t => t.id === selectedTarget.value)?.color || '#d97706'
})

const predictionStats = computed(() => {
  const values = historicalValues.value
  const total = values.reduce((s, v) => s + v, 0)
  const avg = values.length ? Math.round(total / values.length) : 0
  return [
    { label: t('predict.dataPoints'), value: String(values.length) },
    { label: t('predict.average'), value: formatNumber(avg) }
  ]
})
const summaryStats = computed(() => {
  const values = historicalValues.value
  const max = values.length ? Math.max(...values) : 0
  const min = values.length ? Math.min(...values) : 0
  return [
    { label: t('predict.maximum'), value: formatNumber(max) },
    { label: t('predict.minimum'), value: formatNumber(min) }
  ]
})

function generatePrediction() {
  if (historicalValues.value.length < 3) return
  showPrediction.value = true
  const predictions = generatePredictions(selectedModel.value, historicalValues.value, predictionPeriod.value)
  const conf = computeConfidence(predictions, historicalValues.value)
  const now = new Date()
  const labels = []
  for (let i = 1; i <= predictionPeriod.value; i++) {
    const date = new Date(now.getFullYear(), now.getMonth() + i, 1)
    labels.push(`${date.getFullYear()}年${date.getMonth() + 1}月`)
  }
  predictionResults.value = {
    single: { predictions, labels, lower: conf.map(c => c.lower), upper: conf.map(c => c.upper), confidence: conf.map(c => c.confidence) }
  }
}

const mainChartOption = computed(() => {
  if (!showPrediction.value || !historicalData.value.length) return {}
  const allLabels = [...historicalLabels.value]
  const predLabels = predictionResults.value?.single?.labels || []
  allLabels.push(...predLabels)

  const histVals = [...historicalValues.value]
  const preds = predictionResults.value?.single?.predictions || []
  const upper = predictionResults.value?.single?.upper || []
  const lower = predictionResults.value?.single?.lower || []

  const predData = [...Array(histVals.length - 1).fill(null), histVals[histVals.length - 1], ...preds]
  const upperData = [...Array(histVals.length - 1).fill(null), histVals[histVals.length - 1], ...upper]
  const lowerData = [...Array(histVals.length - 1).fill(null), histVals[histVals.length - 1], ...lower]
  const histData = [...histVals, preds[0], ...Array(preds.length - 1).fill(null)]

  const series = [
    {
      name: t('predict.historicalDataLabel'),
      type: 'line',
      data: histData,
      smooth: true,
      lineStyle: { color: selectedTargetColor.value, width: 2.5 },
      itemStyle: { color: selectedTargetColor.value },
      symbol: 'circle',
      symbolSize: 6
    },
    {
      name: t('predict.predictedData'),
      type: 'line',
      data: predData,
      smooth: true,
      lineStyle: { color: '#f59e0b', width: 2.5, type: 'dashed' },
      itemStyle: { color: '#f59e0b' },
      symbol: 'diamond',
      symbolSize: 8,
      areaStyle: { color: 'rgba(245, 158, 11, 0.1)' }
    }
  ]

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let html = `<strong>${params[0].axisValue}</strong><br/>`
        params.forEach(p => {
          if (p.value !== null && p.value !== undefined) {
            html += `${p.marker} ${p.seriesName}: ${formatNumber(p.value)}<br/>`
          }
        })
        return html
      }
    },
    legend: { data: [t('predict.historicalDataLabel'), t('predict.predictedData')], bottom: 0, textStyle: { fontSize: 12 } },
    grid: { left: '3%', right: '4%', top: '8%', bottom: '14%', containLabel: true },
    xAxis: { type: 'category', data: allLabels, boundaryGap: false, axisLabel: { fontSize: 11, rotate: 30 } },
    yAxis: { type: 'value', axisLabel: { formatter: v => formatNumber(v) } },
    series
  }
})

watch(selectedTarget, () => { showPrediction.value = false; predictionResults.value = null })

onMounted(() => { if (props.allData) loading.value = false })
</script>

<template>
  <div class="predict-view">
    <PageHeader :title="t('predict.title')" :description="t('predict.desc')" :loading="loading" @refresh="showPrediction = false; predictionResults = null" />

    <LoadingSpinner :loading="loading">
      <div class="control-bar">
        <div class="control-group">
          <label class="ctrl-label">{{ t('predict.predictionTarget') }}</label>
          <div class="btn-group">
            <button
              v-for="tgt in predictionTargets"
              :key="tgt.id"
              class="ctrl-btn"
              :class="{ active: selectedTarget === tgt.id }"
              @click="selectedTarget = tgt.id"
            >
              {{ t(tgt.label) }}
            </button>
          </div>
        </div>

        <div class="control-group">
          <label class="ctrl-label">{{ t('predict.predictionModel') }}</label>
          <select v-model="selectedModel" class="ctrl-select">
            <option v-for="m in predictionModels" :key="m.id" :value="m.id">{{ t(m.label) }}</option>
          </select>
        </div>

        <div class="control-group">
          <label class="ctrl-label">{{ t('predict.predictionPeriod') }}</label>
          <div class="btn-group">
            <button
              v-for="p in [1, 2, 3, 6, 12]"
              :key="p"
              class="ctrl-btn"
              :class="{ active: predictionPeriod === p }"
              @click="predictionPeriod = p"
            >{{ p }}{{ t('predict.monthsShort') }}</button>
          </div>
        </div>

        <button class="generate-btn" @click="generatePrediction" :disabled="historicalValues.length < 3">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/>
          </svg>
          {{ t('predict.startPrediction') }}
        </button>
      </div>

      <div v-if="historicalValues.length < 3" class="warning-card">
        <svg viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" width="24" height="24">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <div>
          <strong>{{ t('predict.insufficientData') }}</strong>
          <p>{{ t('predict.insufficientDataDesc') }}</p>
        </div>
      </div>

      <template v-if="showPrediction && predictionResults">
        <div class="charts-row">
          <div class="main-chart-col">
            <ChartCard :title="t('predict.predictionChart')" :color="selectedTargetColor" :stats="predictionStats" :delay="0.2">
              <div class="echart-wrap">
                <v-chart class="echart-fill" :option="mainChartOption" autoresize />
              </div>
            </ChartCard>
          </div>
          <div class="summary-col">
            <ChartCard :title="t('predict.forecastSummary')" :color="'var(--color-warning-500)'" :stats="summaryStats" :delay="0.3">
              <div class="summary-stats">
                <div class="summary-item">
                  <span class="s-label">{{ t('predict.averageForecast') }}</span>
                  <span class="s-value">{{ formatNumber(Math.round(predictionResults.single.predictions.reduce((s, v) => s + v, 0) / predictionResults.single.predictions.length)) }}</span>
                </div>
                <div class="summary-item">
                  <span class="s-label">{{ t('predict.totalForecast') }}</span>
                  <span class="s-value">{{ formatNumber(Math.round(predictionResults.single.predictions.reduce((s, v) => s + v, 0))) }}</span>
                </div>
                <div class="summary-item">
                  <span class="s-label">{{ t('predict.trend') }}</span>
                  <span class="s-value" :class="predictionResults.single.predictions.at(-1) > predictionResults.single.predictions[0] ? 'up' : 'down'">
                    {{ predictionResults.single.predictions.at(-1) > predictionResults.single.predictions[0] ? '↑' : '↓' }}
                    {{ Math.abs(((predictionResults.single.predictions.at(-1) - predictionResults.single.predictions[0]) / predictionResults.single.predictions[0] * 100)).toFixed(1) }}%
                  </span>
                </div>
              </div>
              <table class="detail-mini">
                <thead>
                  <tr>
                    <th>{{ t('predict.period') }}</th>
                    <th>{{ t('predict.predictedValue') }}</th>
                    <th>{{ t('predict.lowerBound') }}</th>
                    <th>{{ t('predict.upperBound') }}</th>
                    <th>{{ t('predict.confidence') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(label, idx) in predictionResults.single.labels" :key="label">
                    <td>{{ label }}</td>
                    <td class="val-cell">{{ formatNumber(Math.round(predictionResults.single.predictions[idx])) }}</td>
                    <td>{{ formatNumber(predictionResults.single.lower[idx]) }}</td>
                    <td>{{ formatNumber(predictionResults.single.upper[idx]) }}</td>
                    <td>
                      <span class="conf-badge" :class="predictionResults.single.confidence[idx] >= 80 ? 'high' : predictionResults.single.confidence[idx] >= 60 ? 'med' : 'low'">
                        {{ predictionResults.single.confidence[idx] }}%
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </ChartCard>
          </div>
        </div>


      </template>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.predict-view {
  max-width: var(--main-max-width);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.control-bar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  align-items: flex-end;
  padding: var(--space-3) var(--space-4);
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-neutral-100);
  flex-shrink: 0;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ctrl-label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-500);
  text-transform: uppercase;
}

.btn-group {
  display: flex;
  gap: 3px;
}

.ctrl-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-neutral-200);
  background: var(--color-neutral-0);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-neutral-600);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.ctrl-btn:hover { border-color: var(--color-primary-400); color: var(--color-primary-500); }
.ctrl-btn.active { background: var(--color-primary-500); border-color: var(--color-primary-500); color: #fff; }

.ctrl-select {
  padding: 7px 12px;
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  background: var(--color-neutral-0);
  color: var(--color-neutral-700);
  cursor: pointer;
}

.ctrl-select:focus { outline: none; border-color: var(--color-primary-400); }

.generate-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: none;
  background: var(--gradient-primary);
  color: #fff;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-left: auto;
}

.generate-btn:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3); }
.generate-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.warning-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: #fffbeb;
  border: 1px solid #fbbf24;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.warning-card strong { display: block; font-size: var(--text-sm); font-weight: var(--font-semibold); color: #92400e; }
.warning-card p { margin: 2px 0 0; font-size: var(--text-xs); color: #a16207; }

.charts-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.charts-row :deep(.chart-card) {
  height: 100%;
}

.main-chart-col, .summary-col { min-width: 0; }

.echart-wrap { width: 100%; height: 100%; flex: 1; min-height: 0; }

.echart-compare { height: 100%; }

.echart-fill { width: 100%; height: 100%; min-height: 280px; }

.summary-stats {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-neutral-100);
}

.summary-item { display: flex; justify-content: space-between; align-items: center; }
.s-label { font-size: var(--text-xs); color: var(--color-neutral-500); }
.s-value { font-size: var(--text-base); font-weight: var(--font-bold); color: var(--color-neutral-800); }
.s-value.up { color: #10b981; }
.s-value.down { color: #ef4444; }

.detail-mini { width: 100%; border-collapse: collapse; margin-top: var(--space-2); font-size: var(--text-xs); }
.detail-mini th {
  text-align: left;
  padding: 6px 8px;
  font-size: 10px;
  font-weight: var(--font-semibold);
  color: var(--color-neutral-400);
  border-bottom: 2px solid var(--color-neutral-100);
  text-transform: uppercase;
  white-space: nowrap;
}
.detail-mini td {
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-neutral-50);
  color: var(--color-neutral-600);
}
.val-cell { font-weight: var(--font-semibold); color: #f59e0b; }
.conf-badge { font-size: 10px; font-weight: var(--font-semibold); padding: 2px 6px; border-radius: 4px; }
.conf-badge.high { color: #10b981; background: #ecfdf5; }
.conf-badge.med { color: #f59e0b; background: #fffbeb; }
.conf-badge.low { color: #ef4444; background: #fef2f2; }

@media (max-width: 1200px) {
  .charts-row { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .control-bar { flex-direction: column; align-items: stretch; }
  .generate-btn { margin-left: 0; width: 100%; justify-content: center; }
}
</style>