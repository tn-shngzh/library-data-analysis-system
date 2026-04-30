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
const predictionDimension = ref('active')
const predictionMonths = ref(3)
const showPrediction = ref(false)
const predictionResult = ref(null)

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const monthlyTrend = computed(() => props.allData?.readers?.monthlyTrend || [])

const activeReaderTrend = computed(() => {
  return monthlyTrend.value.map(d => ({ month: d.month, count: d.activeCount || 0 }))
})

const borrowTrend = computed(() => {
  return monthlyTrend.value.map(d => ({ month: d.month, count: d.borrowCount || 0 }))
})

const statCards = computed(() => {
  const activeData = activeReaderTrend.value
  const borrowData = borrowTrend.value
  const activeTotal = activeData.reduce((s, d) => s + (d.count || 0), 0)
  const activeAvg = activeData.length ? Math.round(activeTotal / activeData.length) : 0
  const borrowTotal = borrowData.reduce((s, d) => s + (d.count || 0), 0)
  const borrowAvg = borrowData.length ? Math.round(borrowTotal / borrowData.length) : 0
  return [
    { i18nKey: 'predict.historicalData', value: activeData.length + ' ' + t('predict.months'), icon: 'database', color: '#d97706' },
    { i18nKey: 'predict.activeReaderAvg', value: formatNumber(activeAvg), icon: 'avg', color: '#3b82f6' },
    { i18nKey: 'predict.borrowAvg', value: formatNumber(borrowAvg), icon: 'avg', color: '#10b981' },
    { i18nKey: 'predict.predictionPeriod', value: predictionMonths.value + ' ' + t('predict.months'), icon: 'calendar', color: '#f59e0b' }
  ]
})

const generatePrediction = () => {
  const activeData = activeReaderTrend.value
  const borrowData = borrowTrend.value
  if (activeData.length < 3 || borrowData.length < 3) return

  showPrediction.value = true
  const activeCounts = activeData.map(d => d.count || 0)
  const borrowCounts = borrowData.map(d => d.count || 0)

  const lastMonthLabel = monthlyTrend.value[monthlyTrend.value.length - 1]?.month || ''
  const nextMonthNums = []
  const yearMatch = lastMonthLabel.match(/(\d+)年(\d+)/)
  if (yearMatch) {
    let y = parseInt(yearMatch[1])
    let m = parseInt(yearMatch[2])
    for (let i = 1; i <= predictionMonths.value; i++) {
      m++
      if (m > 12) { m = 1; y++ }
      nextMonthNums.push({ label: `${y}年${m}`, monthIdx: m })
    }
  } else {
    const mMatch = lastMonthLabel.match(/(\d+)/)
    const startM = mMatch ? parseInt(mMatch[1]) : 12
    for (let i = 1; i <= predictionMonths.value; i++) {
      const m = startM + i
      nextMonthNums.push({ label: `${m}${t('predict.month')}`, monthIdx: ((m - 1) % 12) + 1 })
    }
  }

  const computeCI = (values, predicted, step) => {
    const n = values.length
    if (n < 2) return { lower: Math.max(0, Math.round(predicted * 0.8)), upper: Math.round(predicted * 1.2) }
    const xMean = (n + 1) / 2
    const yMean = values.reduce((s, v) => s + v, 0) / n
    let num = 0, den = 0
    for (let i = 0; i < n; i++) {
      num += (i + 1 - xMean) * (values[i] - yMean)
      den += (i + 1 - xMean) ** 2
    }
    const slope = den !== 0 ? num / den : 0
    const intercept = yMean - slope * xMean
    let ssRes = 0
    for (let i = 0; i < n; i++) {
      const predicted_i = slope * (i + 1) + intercept
      ssRes += (values[i] - predicted_i) ** 2
    }
    const se = Math.sqrt(ssRes / Math.max(1, n - 2))
    const tValue = n >= 30 ? 1.96 : n >= 10 ? 2.228 : n >= 5 ? 2.776 : 4.303
    const margin = tValue * se * Math.sqrt(1 + 1 / n + ((n + step) - xMean) ** 2 / den)
    return {
      lower: Math.max(0, Math.round(predicted - margin)),
      upper: Math.round(predicted + margin)
    }
  }

  let activePredictions = []
  let borrowPredictions = []
  
  if (activeModel.value === 'moving_avg') {
    const windowSize = 3
    const lastActiveValues = activeCounts.slice(-windowSize)
    const activeAvg = lastActiveValues.reduce((s, v) => s + v, 0) / windowSize
    const activeTrend = activeCounts.length >= 6
      ? (activeCounts.slice(-3).reduce((s, v) => s + v, 0) - activeCounts.slice(-6, -3).reduce((s, v) => s + v, 0)) / 3
      : 0
    const decay = activeCounts.length >= 6
      ? Math.min(0.5, Math.abs(activeTrend) / (activeAvg || 1))
      : 0.3

    const lastBorrowValues = borrowCounts.slice(-windowSize)
    const borrowAvg = lastBorrowValues.reduce((s, v) => s + v, 0) / windowSize
    const borrowTrendVal = borrowCounts.length >= 6
      ? (borrowCounts.slice(-3).reduce((s, v) => s + v, 0) - borrowCounts.slice(-6, -3).reduce((s, v) => s + v, 0)) / 3
      : 0
    const borrowDecay = borrowCounts.length >= 6
      ? Math.min(0.5, Math.abs(borrowTrendVal) / (borrowAvg || 1))
      : 0.3

    for (let i = 1; i <= predictionMonths.value; i++) {
      const activePredicted = Math.max(0, Math.round(activeAvg + activeTrend * i * decay))
      const borrowPredicted = Math.max(0, Math.round(borrowAvg + borrowTrendVal * i * borrowDecay))
      const activeCI = computeCI(activeCounts, activePredicted, i)
      const borrowCI = computeCI(borrowCounts, borrowPredicted, i)
      const confidence = Math.max(60, 95 - i * 10)
      
      activePredictions.push({
        month: nextMonthNums[i - 1].label,
        predicted: activePredicted,
        lower: activeCI.lower,
        upper: activeCI.upper,
        confidence
      })
      
      borrowPredictions.push({
        month: nextMonthNums[i - 1].label,
        predicted: borrowPredicted,
        lower: borrowCI.lower,
        upper: borrowCI.upper,
        confidence
      })
    }
  } else if (activeModel.value === 'seasonal') {
    const period = 12
    const computeSeasonal = (counts) => {
      if (counts.length < period) {
        const avg = counts.reduce((s, v) => s + v, 0) / counts.length
        return Array(period).fill(avg / (avg || 1))
      }
      const seasonSums = Array(period).fill(0)
      const seasonCounts = Array(period).fill(0)
      for (let i = 0; i < counts.length; i++) {
        const seasonIdx = i % period
        seasonSums[seasonIdx] += counts[i]
        seasonCounts[seasonIdx]++
      }
      const seasonAvgs = seasonSums.map((s, i) => seasonCounts[i] ? s / seasonCounts[i] : 0)
      const overallAvg = seasonAvgs.reduce((s, v) => s + v, 0) / period
      return seasonAvgs.map(v => overallAvg ? v / overallAvg : 1)
    }

    const activeSeasonal = computeSeasonal(activeCounts)
    const borrowSeasonal = computeSeasonal(borrowCounts)
    const activeBase = activeCounts.slice(-3).reduce((s, v) => s + v, 0) / 3
    const borrowBase = borrowCounts.slice(-3).reduce((s, v) => s + v, 0) / 3
    const lastIdx = activeCounts.length - 1

    for (let i = 1; i <= predictionMonths.value; i++) {
      const seasonIdx = (lastIdx + i) % period
      const activePredicted = Math.max(0, Math.round(activeBase * activeSeasonal[seasonIdx]))
      const borrowPredicted = Math.max(0, Math.round(borrowBase * borrowSeasonal[seasonIdx]))
      const activeCI = computeCI(activeCounts, activePredicted, i)
      const borrowCI = computeCI(borrowCounts, borrowPredicted, i)
      const confidence = Math.max(55, 90 - i * 8)
      
      activePredictions.push({
        month: nextMonthNums[i - 1].label,
        predicted: activePredicted,
        lower: activeCI.lower,
        upper: activeCI.upper,
        confidence
      })
      
      borrowPredictions.push({
        month: nextMonthNums[i - 1].label,
        predicted: borrowPredicted,
        lower: borrowCI.lower,
        upper: borrowCI.upper,
        confidence
      })
    }
  } else {
    const n = activeCounts.length
    const xMean = (n + 1) / 2
    const activeYMean = activeCounts.reduce((s, v) => s + v, 0) / n
    const borrowYMean = borrowCounts.reduce((s, v) => s + v, 0) / n
    
    let activeNum = 0, activeDen = 0
    let borrowNum = 0, borrowDen = 0
    for (let i = 0; i < n; i++) {
      activeNum += (i + 1 - xMean) * (activeCounts[i] - activeYMean)
      activeDen += (i + 1 - xMean) ** 2
      borrowNum += (i + 1 - xMean) * (borrowCounts[i] - borrowYMean)
      borrowDen += (i + 1 - xMean) ** 2
    }
    
    const activeSlope = activeDen !== 0 ? activeNum / activeDen : 0
    const activeIntercept = activeYMean - activeSlope * xMean
    const borrowSlope = borrowDen !== 0 ? borrowNum / borrowDen : 0
    const borrowIntercept = borrowYMean - borrowSlope * xMean

    for (let i = 1; i <= predictionMonths.value; i++) {
      const x = n + i
      const activePredicted = Math.max(0, Math.round(activeSlope * x + activeIntercept))
      const borrowPredicted = Math.max(0, Math.round(borrowSlope * x + borrowIntercept))
      const activeCI = computeCI(activeCounts, activePredicted, i)
      const borrowCI = computeCI(borrowCounts, borrowPredicted, i)
      const confidence = Math.max(55, 92 - i * 12)
      
      activePredictions.push({
        month: nextMonthNums[i - 1].label,
        predicted: activePredicted,
        lower: activeCI.lower,
        upper: activeCI.upper,
        confidence
      })
      
      borrowPredictions.push({
        month: nextMonthNums[i - 1].label,
        predicted: borrowPredicted,
        lower: borrowCI.lower,
        upper: borrowCI.upper,
        confidence
      })
    }
  }

  predictionResult.value = {
    active: activePredictions,
    borrow: borrowPredictions
  }
}

const chartWidth = 800
const chartHeight = 300
const padding = 50

const combinedChartPaths = computed(() => {
  const activeData = activeReaderTrend.value
  const borrowData = borrowTrend.value
  const pred = predictionResult.value
  if (!activeData.length && !borrowData.length) return { activeLinePath: '', activeAreaPath: '', borrowLinePath: '', borrowAreaPath: '', activePredPath: '', borrowPredPath: '', activePoints: [], borrowPoints: [], activePredPoints: [], borrowPredPoints: [] }

  const activeValues = activeData.map(d => d.count || 0)
  const borrowValues = borrowData.map(d => d.count || 0)
  const allValues = [
    ...activeValues,
    ...borrowValues,
    ...(pred?.active?.map(p => p.upper || 0) || []),
    ...(pred?.borrow?.map(p => p.upper || 0) || [])
  ]
  const maxVal = Math.max(...allValues) || 1
  const totalPoints = activeData.length + (pred?.active?.length || 0)
  const chartW = chartWidth - padding * 2
  const chartH = chartHeight - padding * 2

  const activePoints = activeData.map((d, i) => ({
    x: padding + (i / (totalPoints - 1 || 1)) * chartW,
    y: padding + chartH - ((d.count || 0) / maxVal) * chartH,
    label: d.month,
    value: d.count || 0,
    type: 'actual'
  }))

  const borrowPoints = borrowData.map((d, i) => ({
    x: padding + (i / (totalPoints - 1 || 1)) * chartW,
    y: padding + chartH - ((d.count || 0) / maxVal) * chartH,
    label: d.month,
    value: d.count || 0,
    type: 'actual'
  }))

  const lastActive = activePoints[activePoints.length - 1]
  const lastBorrow = borrowPoints[borrowPoints.length - 1]
  
  const activePredPoints = (pred?.active || []).map((p, i) => ({
    x: padding + ((activeData.length + i) / (totalPoints - 1 || 1)) * chartW,
    y: padding + chartH - (p.predicted / maxVal) * chartH,
    label: p.month,
    value: p.predicted,
    upper: padding + chartH - (p.upper / maxVal) * chartH,
    lower: padding + chartH - (p.lower / maxVal) * chartH,
    type: 'predicted'
  }))

  const borrowPredPoints = (pred?.borrow || []).map((p, i) => ({
    x: padding + ((borrowData.length + i) / (totalPoints - 1 || 1)) * chartW,
    y: padding + chartH - (p.predicted / maxVal) * chartH,
    label: p.month,
    value: p.predicted,
    upper: padding + chartH - (p.upper / maxVal) * chartH,
    lower: padding + chartH - (p.lower / maxVal) * chartH,
    type: 'predicted'
  }))

  const activeLinePath = activePoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const activeAreaPath = activeLinePath +
    ` L ${activePoints[activePoints.length - 1]?.x || padding} ${padding + chartH}` +
    ` L ${activePoints[0].x} ${padding + chartH} Z`

  const borrowLinePath = borrowPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  const borrowAreaPath = borrowLinePath +
    ` L ${borrowPoints[borrowPoints.length - 1]?.x || padding} ${padding + chartH}` +
    ` L ${borrowPoints[0].x} ${padding + chartH} Z`

  let activePredPath = ''
  if (activePredPoints.length && lastActive) {
    activePredPath = `M ${lastActive.x} ${lastActive.y} ` +
      activePredPoints.map(p => `L ${p.x} ${p.y}`).join(' ')
  }

  let borrowPredPath = ''
  if (borrowPredPoints.length && lastBorrow) {
    borrowPredPath = `M ${lastBorrow.x} ${lastBorrow.y} ` +
      borrowPredPoints.map(p => `L ${p.x} ${p.y}`).join(' ')
  }

  return { 
    activeLinePath, 
    activeAreaPath, 
    borrowLinePath, 
    borrowAreaPath, 
    activePredPath, 
    borrowPredPath, 
    activePoints, 
    borrowPoints, 
    activePredPoints, 
    borrowPredPoints, 
    maxVal 
  }
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
            <label>{{ t('predict.predictionDimension') }}</label>
            <div class="model-options">
              <button
                class="model-btn btn-select"
                :class="{ active: predictionDimension === 'active' }"
                @click="predictionDimension = 'active'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <span>{{ t('predict.activeReaders') }}</span>
                <small>{{ t('predict.activeReadersDesc') }}</small>
              </button>
              <button
                class="model-btn btn-select"
                :class="{ active: predictionDimension === 'borrow' }"
                @click="predictionDimension = 'borrow'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                </svg>
                <span>{{ t('predict.borrowCount') }}</span>
                <small>{{ t('predict.borrowCountDesc') }}</small>
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>{{ t('predict.predictionModel') }}</label>
            <div class="model-options">
              <button
                class="model-btn btn-select"
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
                class="model-btn btn-select"
                :class="{ active: activeModel === 'linear' }"
                @click="activeModel = 'linear'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="5" y1="19" x2="19" y2="5"/>
                </svg>
                <span>{{ t('predict.linearRegression') }}</span>
                <small>{{ t('predict.linearRegressionDesc') }}</small>
              </button>
              <button
                class="model-btn btn-select"
                :class="{ active: activeModel === 'seasonal' }"
                @click="activeModel = 'seasonal'"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
                <span>{{ t('predict.seasonalAvg') }}</span>
                <small>{{ t('predict.seasonalAvgDesc') }}</small>
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>{{ t('predict.predictionPeriod') }}</label>
            <div class="month-selector">
              <button
                v-for="m in [1, 2, 3, 6]"
                :key="m"
                class="month-btn btn-select btn-sm"
                :class="{ active: predictionMonths === m }"
                @click="predictionMonths = m"
              >{{ m }}{{ t('predict.monthsShort') }}</button>
            </div>
          </div>
          <button class="predict-btn btn btn-primary btn-lg" @click="generatePrediction" :disabled="monthlyTrend.length < 3">
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
          <span class="card-subtitle">{{ activeModel === 'moving_avg' ? t('predict.movingAvgModel') : activeModel === 'seasonal' ? t('predict.seasonalAvgModel') : t('predict.linearRegressionModel') }} - {{ predictionDimension === 'active' ? t('predict.activeReaders') : t('predict.borrowCount') }}</span>
        </div>
        <div class="chart-container">
          <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="predict-chart">
            <defs>
              <linearGradient id="activeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#d97706" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#d97706" stop-opacity="0.02"/>
              </linearGradient>
              <linearGradient id="borrowGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"/>
                <stop offset="100%" stop-color="#10b981" stop-opacity="0.02"/>
              </linearGradient>
            </defs>
            <g class="grid-lines">
              <line v-for="i in 5" :key="'grid-' + i"
                :x1="padding" :y1="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                :x2="chartWidth - padding" :y2="padding + (chartHeight - padding * 2) * (i - 1) / 4"
                stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4 4"
              />
            </g>
            <g v-if="predictionDimension === 'active'">
              <path :d="combinedChartPaths.activeAreaPath" fill="url(#activeGrad)" />
              <path :d="combinedChartPaths.activeLinePath" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              <path v-if="combinedChartPaths.activePredPath" :d="combinedChartPaths.activePredPath" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="8 4" stroke-linecap="round" stroke-linejoin="round" />
              <g v-for="(pt, idx) in combinedChartPaths.activePoints" :key="'actual-' + idx">
                <circle :cx="pt.x" :cy="pt.y" r="4" fill="#d97706" />
                <text :x="pt.x" :y="chartHeight - 3" text-anchor="middle" font-size="12" fill="#64748b" font-weight="500" :transform="'rotate(-30,' + pt.x + ',' + (chartHeight - 3) + ')'">{{ pt.label }}</text>
              </g>
              <g v-for="(pt, idx) in combinedChartPaths.activePredPoints" :key="'pred-' + idx">
                <circle :cx="pt.x" :cy="pt.y" r="5" fill="#f59e0b" stroke="white" stroke-width="2" />
                <line v-if="pt.upper && pt.lower" :x1="pt.x" :y1="pt.upper" :x2="pt.x" :y2="pt.lower" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
                <line v-if="pt.upper && pt.lower" :x1="pt.x - 4" :y1="pt.upper" :x2="pt.x + 4" :y2="pt.upper" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
                <line v-if="pt.upper && pt.lower" :x1="pt.x - 4" :y1="pt.lower" :x2="pt.x + 4" :y2="pt.lower" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
                <text :x="pt.x" :y="chartHeight - 3" text-anchor="middle" font-size="12" fill="#f59e0b" font-weight="600" :transform="'rotate(-30,' + pt.x + ',' + (chartHeight - 3) + ')'">{{ pt.label }}</text>
              </g>
            </g>
            <g v-else>
              <path :d="combinedChartPaths.borrowAreaPath" fill="url(#borrowGrad)" />
              <path :d="combinedChartPaths.borrowLinePath" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              <path v-if="combinedChartPaths.borrowPredPath" :d="combinedChartPaths.borrowPredPath" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="8 4" stroke-linecap="round" stroke-linejoin="round" />
              <g v-for="(pt, idx) in combinedChartPaths.borrowPoints" :key="'actual-' + idx">
                <circle :cx="pt.x" :cy="pt.y" r="4" fill="#10b981" />
                <text :x="pt.x" :y="chartHeight - 3" text-anchor="middle" font-size="12" fill="#64748b" font-weight="500" :transform="'rotate(-30,' + pt.x + ',' + (chartHeight - 3) + ')'">{{ pt.label }}</text>
              </g>
              <g v-for="(pt, idx) in combinedChartPaths.borrowPredPoints" :key="'pred-' + idx">
                <circle :cx="pt.x" :cy="pt.y" r="5" fill="#f59e0b" stroke="white" stroke-width="2" />
                <line v-if="pt.upper && pt.lower" :x1="pt.x" :y1="pt.upper" :x2="pt.x" :y2="pt.lower" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
                <line v-if="pt.upper && pt.lower" :x1="pt.x - 4" :y1="pt.upper" :x2="pt.x + 4" :y2="pt.upper" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
                <line v-if="pt.upper && pt.lower" :x1="pt.x - 4" :y1="pt.lower" :x2="pt.x + 4" :y2="pt.lower" stroke="#f59e0b" stroke-width="1.5" opacity="0.5" />
                <text :x="pt.x" :y="chartHeight - 3" text-anchor="middle" font-size="12" fill="#f59e0b" font-weight="600" :transform="'rotate(-30,' + pt.x + ',' + (chartHeight - 3) + ')'">{{ pt.label }}</text>
              </g>
            </g>
          </svg>
        </div>

        <div class="legend-bar">
          <div class="legend-item">
            <span class="legend-dot actual active"></span>
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
          <span class="card-subtitle">{{ predictionDimension === 'active' ? t('predict.activeReaders') : t('predict.borrowCount') }}</span>
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
            <tr v-for="item in (predictionDimension === 'active' ? predictionResult.active : predictionResult.borrow)" :key="item.month">
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
  border-top-color: #d97706;
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
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.model-btn svg {
  width: 24px;
  height: 24px;
  color: var(--color-primary-500);
  margin-bottom: 4px;
}

.model-btn span {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-neutral-800);
}

.model-btn small {
  font-size: 12px;
  color: var(--color-neutral-400);
}

.month-selector {
  display: flex;
  gap: 8px;
}

.month-btn.active {
  background: var(--color-primary-500);
  color: var(--color-neutral-0);
  border-color: var(--color-primary-500);
}

.predict-btn svg {
  width: 18px;
  height: 18px;
}

.warning-card {
  border-color: var(--color-primary-400);
  background: var(--color-primary-50);
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

.legend-dot.actual.active {
  background: #d97706;
}

.legend-dot.actual.borrow {
  background: #10b981;
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
