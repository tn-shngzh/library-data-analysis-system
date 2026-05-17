<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { analysisApi } from '@/api/analysis'
import { formatNumber } from '@/utils/format'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'
import ChartViewSwitcher from '@/components/ChartViewSwitcher.vue'

const { t } = useI18n()

const loading = ref(false)
const activeTab = ref('correlation')
const correlationSubView = ref('bar')
const comparisonSubView = ref('bar')
const heatmapSubView = ref('heatmap')

const correlationData = ref({ reader_type_borrow: [], action_distribution: [] })
const degreeTrendData = ref({ months: [], series: [] })
const comparisonData = ref({ period1: {}, period2: {}, changes: {} })
const dailyTrendData = ref({ dates: [], total: [], borrowed: [], returned: [] })
const catComparisonData = ref({ comparison: [] })
const heatmapData = ref({ categories: [], months: [], values: [] })

const period1Start = ref('')
const period1End = ref('')
const period2Start = ref('')
const period2End = ref('')

const tabs = [
  { id: 'correlation', i18nKey: 'analysis.correlation' },
  { id: 'comparison', i18nKey: 'analysis.comparison' },
  { id: 'heatmap', i18nKey: 'analysis.heatmap' }
]

const correlationViews = [
  { key: 'bar', label: t('analysis.viewBar'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { key: 'line', label: t('analysis.viewLine'), icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' },
  { key: 'pie', label: t('analysis.viewPie'), icon: '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>' },
  { key: 'radar', label: t('analysis.viewRadar'), icon: '<polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="8.5" x2="22" y2="8.5"/>' }
]

const comparisonViews = [
  { key: 'bar', label: t('analysis.viewBar'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { key: 'line', label: t('analysis.viewLine'), icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' },
  { key: 'ranking', label: t('analysis.viewRanking'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' }
]

const heatmapViews = [
  { key: 'heatmap', label: t('analysis.viewHeatmap'), icon: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>' },
  { key: 'stacked', label: t('analysis.viewStacked'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { key: 'line', label: t('analysis.viewLine'), icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' }
]

const fetchAll = async () => {
  loading.value = true
  try {
    await Promise.all([fetchCorrelation(), fetchDegreeTrend(), fetchComparison(), fetchDailyTrend(), fetchCatComparison(), fetchHeatmap()])
  } finally {
    loading.value = false
  }
}

const fetchCorrelation = async () => {
  try {
    const data = await analysisApi.getCorrelation()
    if (data) correlationData.value = data
  } catch (e) { console.error('Failed to fetch correlation data', e) }
}

const fetchDegreeTrend = async () => {
  try {
    const data = await analysisApi.getDegreeMonthlyTrend()
    if (data) degreeTrendData.value = data
  } catch (e) { console.error('Failed to fetch degree trend', e) }
}

const fetchComparison = async () => {
  try {
    const data = await analysisApi.getPeriodComparison(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined,
      period2Start.value ? parseInt(period2Start.value) : undefined,
      period2End.value ? parseInt(period2End.value) : undefined
    )
    if (data) comparisonData.value = data
  } catch (e) { console.error('Failed to fetch comparison data', e) }
}

const fetchDailyTrend = async () => {
  try {
    const data = await analysisApi.getDailyTrend(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined
    )
    if (data) dailyTrendData.value = data
  } catch (e) { console.error('Failed to fetch daily trend', e) }
}

const fetchCatComparison = async () => {
  try {
    const data = await analysisApi.getCategoryPeriodComparison(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined,
      period2Start.value ? parseInt(period2Start.value) : undefined,
      period2End.value ? parseInt(period2End.value) : undefined
    )
    if (data) catComparisonData.value = data
  } catch (e) { console.error('Failed to fetch cat comparison', e) }
}

const fetchHeatmap = async () => {
  try {
    const data = await analysisApi.getCategoryHeatmap()
    if (data) heatmapData.value = data
  } catch (e) { console.error('Failed to fetch heatmap data', e) }
}

const refreshTabData = () => {
  if (activeTab.value === 'correlation') {
    fetchCorrelation()
    fetchDegreeTrend()
  } else if (activeTab.value === 'comparison') {
    fetchComparison()
    fetchDailyTrend()
    fetchCatComparison()
  } else {
    fetchHeatmap()
  }
}

const CHART_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

const barOption = computed(() => {
  const data = correlationData.value.reader_type_borrow || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: [t('analysis.checkout'), t('analysis.checkin')], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.degree_name), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: t('analysis.totalBorrow') },
    series: [
      { name: t('analysis.checkout'), type: 'bar', data: data.map(d => d.borrowed || 0), itemStyle: { color: '#5470c6', borderRadius: [4, 4, 0, 0] }, barGap: '20%' },
      { name: t('analysis.checkin'), type: 'bar', data: data.map(d => d.returned || 0), itemStyle: { color: '#91cc75', borderRadius: [4, 4, 0, 0] } }
    ]
  }
})

const lineOption = computed(() => {
  const months = degreeTrendData.value.months || []
  const series = (degreeTrendData.value.series || []).map((s, i) => ({
    name: s.name,
    type: 'line',
    data: s.data,
    smooth: true,
    lineStyle: { width: 3 },
    itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    symbol: 'circle',
    symbolSize: 6
  }))
  return {
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', bottom: 0, data: series.map(s => s.name) },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: months, boundaryGap: false },
    yAxis: { type: 'value', name: t('analysis.totalBorrow') },
    series
  }
})

const pieOption = computed(() => {
  const data = (correlationData.value.action_distribution || []).map(d => ({
    name: d.name,
    value: d.count
  }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}\n{d}%' },
      emphasis: { label: { fontSize: 18, fontWeight: 'bold' } },
      data,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 }
    }]
  }
})

const radarOption = computed(() => {
  const data = correlationData.value.reader_type_borrow || []
  const indicators = [
    { name: t('analysis.checkout'), max: Math.max(...data.map(d => d.borrowed || 0), 1) * 1.2 },
    { name: t('analysis.checkin'), max: Math.max(...data.map(d => d.returned || 0), 1) * 1.2 },
    { name: t('analysis.avgPerReader'), max: Math.max(...data.map(d => d.avg_per_reader || 0), 1) * 1.2 },
    { name: t('analysis.activeReaders'), max: Math.max(...data.map(d => d.reader_count || 0), 1) * 1.2 }
  ]
  const seriesData = data.map((d, i) => ({
    name: d.degree_name,
    value: [d.borrowed || 0, d.returned || 0, d.avg_per_reader || 0, d.reader_count || 0],
    lineStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    areaStyle: { color: CHART_COLORS[i % CHART_COLORS.length], opacity: 0.1 }
  }))
  return {
    tooltip: {},
    legend: { bottom: 0, data: data.map(d => d.degree_name) },
    radar: { indicator: indicators, center: ['50%', '48%'], radius: '62%' },
    series: [{ type: 'radar', data: seriesData }]
  }
})

const comparisonBarOption = computed(() => {
  const p1 = comparisonData.value.period1 || {}
  const p2 = comparisonData.value.period2 || {}
  const labels = [t('analysis.totalCirculation'), t('analysis.checkoutCount'), t('analysis.returnCount'), t('analysis.activeReaders')]
  const keys = ['total', 'borrowed', 'returned', 'active_readers']
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: [t('analysis.period1'), t('analysis.period2')], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: t('analysis.quantity') },
    series: [
      { name: t('analysis.period1'), type: 'bar', data: keys.map(k => p1[k] || 0), itemStyle: { color: '#5470c6', borderRadius: [4, 4, 0, 0] }, barGap: '20%' },
      { name: t('analysis.period2'), type: 'bar', data: keys.map(k => p2[k] || 0), itemStyle: { color: '#91cc75', borderRadius: [4, 4, 0, 0] } }
    ]
  }
})

const comparisonLineOption = computed(() => {
  const dates = dailyTrendData.value.dates || []
  const total = dailyTrendData.value.total || []
  const borrowed = dailyTrendData.value.borrowed || []
  const returned = dailyTrendData.value.returned || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, data: [t('analysis.totalCircShort'), t('analysis.checkout'), t('analysis.checkin')] },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', name: t('analysis.quantity') },
    series: [
      { name: t('analysis.totalCircShort'), type: 'line', data: total, smooth: true, lineStyle: { width: 3, color: '#5470c6' }, symbol: 'circle', symbolSize: 4 },
      { name: t('analysis.checkout'), type: 'line', data: borrowed, smooth: true, lineStyle: { width: 2, color: '#91cc75' }, symbol: 'circle', symbolSize: 3 },
      { name: t('analysis.checkin'), type: 'line', data: returned, smooth: true, lineStyle: { width: 2, color: '#fac858' }, symbol: 'circle', symbolSize: 3 }
    ]
  }
})

const comparisonRankingOption = computed(() => {
  const items = (catComparisonData.value.comparison || []).slice(0, 12)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        const item = items[p.dataIndex]
        if (!item) return ''
        return `${item.category}<br/>${t('analysis.period1')}: ${item.period1_count}<br/>${t('analysis.period2')}: ${item.period2_count}<br/>${t('analysis.changeRate')}: ${item.change >= 0 ? '+' : ''}${item.change}%`
      }
    },
    grid: { left: '3%', right: '8%', bottom: '8%', top: '6%', containLabel: true },
    xAxis: { type: 'value', name: t('analysis.changeRate') + '(%)' },
    yAxis: {
      type: 'category',
      data: items.map(d => d.category).reverse(),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: items.map(d => d.change).reverse(),
      itemStyle: {
        color: (params) => {
          const reversed = items.slice().reverse()
          const val = reversed[params.dataIndex]?.change || 0
          return val >= 0 ? '#91cc75' : '#ee6666'
        },
        borderRadius: [0, 4, 4, 0]
      },
      label: { show: true, position: 'right', formatter: '{c}%', fontSize: 12 }
    }]
  }
})

const heatmapOption = computed(() => {
  const categories = heatmapData.value.categories || []
  const months = heatmapData.value.months || []
  const values = heatmapData.value.values || []
  const data = []
  let maxVal = 1
  categories.forEach((cat, ci) => {
    (values[ci] || []).forEach((val, mi) => {
      data.push([mi, ci, val])
      if (val > maxVal) maxVal = val
    })
  })
  return {
    tooltip: {
      position: 'top',
      formatter: (p) => `${categories[p.value[1]]} - ${months[p.value[0]]}<br/>${t('analysis.totalBorrow')}: ${p.value[2]}`
    },
    grid: { left: '12%', right: '5%', bottom: '10%', top: '6%' },
    xAxis: { type: 'category', data: months, splitArea: { show: true } },
    yAxis: { type: 'category', data: categories, splitArea: { show: true } },
    visualMap: {
      min: 0,
      max: maxVal,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#f0f9ff', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0284c7'] }
    },
    series: [{
      type: 'heatmap',
      data,
      label: { show: true, fontSize: 10 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } }
    }]
  }
})

const stackedBarOption = computed(() => {
  const categories = heatmapData.value.categories || []
  const months = heatmapData.value.months || []
  const values = heatmapData.value.values || []
  const series = categories.map((cat, ci) => ({
    name: cat,
    type: 'bar',
    data: values[ci] || [],
    stack: 'total',
    emphasis: { focus: 'series' }
  }))
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { type: 'scroll', bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '6%', containLabel: true },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', name: t('analysis.totalBorrow') },
    series
  }
})

const heatmapLineOption = computed(() => {
  const categories = heatmapData.value.categories || []
  const months = heatmapData.value.months || []
  const values = heatmapData.value.values || []
  const series = categories.map((cat, ci) => ({
    name: cat,
    type: 'line',
    data: values[ci] || [],
    smooth: true,
    symbol: 'circle',
    symbolSize: 5
  }))
  return {
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '6%', containLabel: true },
    xAxis: { type: 'category', data: months, boundaryGap: false },
    yAxis: { type: 'value', name: t('analysis.totalBorrow') },
    series
  }
})

const switchTab = (tabId) => {
  activeTab.value = tabId
  refreshTabData()
}

const comparePeriods = () => {
  fetchComparison()
  fetchDailyTrend()
  fetchCatComparison()
}

onMounted(() => {
  fetchAll()
})
</script>

<template>
  <div class="analysis-view">
    <PageHeader
      :title="t('analysis.title')"
      :description="t('analysis.desc')"
      :loading="loading"
      @refresh="refreshTabData"
    />

    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="switchTab(tab.id)"
      >
        {{ t(tab.i18nKey) }}
      </button>
    </div>

    <LoadingSpinner :loading="loading">
      <div v-if="activeTab === 'correlation'" class="tab-content">
        <ChartCard :title="t('analysis.readerTypeBorrow')" color="#5470c6">
          <template #actions>
            <ChartViewSwitcher v-model="correlationSubView" :views="correlationViews" />
          </template>
          <div class="chart-stage">
            <v-chart v-if="correlationSubView === 'bar'" class="full-chart" :option="barOption" autoresize />
            <v-chart v-else-if="correlationSubView === 'line'" class="full-chart" :option="lineOption" autoresize />
            <v-chart v-else-if="correlationSubView === 'pie'" class="full-chart" :option="pieOption" autoresize />
            <v-chart v-else-if="correlationSubView === 'radar'" class="full-chart" :option="radarOption" autoresize />
          </div>
        </ChartCard>
      </div>

      <div v-if="activeTab === 'comparison'" class="tab-content">
        <div class="period-controls">
          <div class="period-group">
            <label>{{ t('analysis.period1') }}</label>
            <div class="input-row">
              <input v-model="period1Start" type="number" :placeholder="t('analysis.startPlaceholder')" class="period-input" />
              <span class="input-sep">-</span>
              <input v-model="period1End" type="number" :placeholder="t('analysis.endPlaceholder')" class="period-input" />
            </div>
          </div>
          <div class="period-group">
            <label>{{ t('analysis.period2') }}</label>
            <div class="input-row">
              <input v-model="period2Start" type="number" :placeholder="t('analysis.startPlaceholder')" class="period-input" />
              <span class="input-sep">-</span>
              <input v-model="period2End" type="number" :placeholder="t('analysis.endPlaceholder')" class="period-input" />
            </div>
          </div>
          <button class="compare-btn" @click="comparePeriods">{{ t('analysis.compare') }}</button>
        </div>

        <ChartCard :title="t('analysis.comparison')" color="#3ba272">
          <template #actions>
            <ChartViewSwitcher v-model="comparisonSubView" :views="comparisonViews" />
          </template>
          <div class="chart-stage">
            <v-chart v-if="comparisonSubView === 'bar'" class="full-chart" :option="comparisonBarOption" autoresize />
            <v-chart v-else-if="comparisonSubView === 'line'" class="full-chart" :option="comparisonLineOption" autoresize />
            <v-chart v-else-if="comparisonSubView === 'ranking'" class="full-chart" :option="comparisonRankingOption" autoresize />
          </div>
        </ChartCard>
      </div>

      <div v-if="activeTab === 'heatmap'" class="tab-content">
        <ChartCard :title="t('analysis.categoryHeatmap')" color="#0ea5e9">
          <template #actions>
            <ChartViewSwitcher v-model="heatmapSubView" :views="heatmapViews" />
          </template>
          <div class="chart-stage">
            <v-chart v-if="heatmapSubView === 'heatmap'" class="full-chart heatmap-chart" :option="heatmapOption" autoresize />
            <v-chart v-else-if="heatmapSubView === 'stacked'" class="full-chart" :option="stackedBarOption" autoresize />
            <v-chart v-else-if="heatmapSubView === 'line'" class="full-chart" :option="heatmapLineOption" autoresize />
          </div>
        </ChartCard>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.analysis-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.tab-nav {
  display: flex;
  gap: 4px;
  background: var(--color-neutral-100);
  border-radius: var(--radius-lg);
  padding: 4px;
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
  transition: all 0.2s;
}

.tab-btn.active {
  background: var(--color-neutral-0);
  color: var(--color-neutral-900);
  box-shadow: var(--shadow-sm);
}

.tab-btn:hover:not(.active) {
  color: var(--color-neutral-700);
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  flex: 1;
  min-height: 0;
}

.tab-content :deep(.chart-card) {
  flex: 1;
  min-height: 0;
}

.chart-stage {
  width: 100%;
  flex: 1;
  min-height: 0;
}

.full-chart {
  width: 100%;
  height: 100%;
  min-height: 360px;
}

.heatmap-chart {
  min-height: 420px;
}

.period-controls {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  align-items: flex-end;
  padding: var(--space-4);
  background: var(--chart-bg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-neutral-200);
  flex-shrink: 0;
}

.period-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.period-group label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
}

.input-row {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.period-input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  width: 130px;
  background: var(--color-neutral-0);
  color: var(--color-neutral-900);
}

.period-input:focus {
  outline: none;
  border-color: var(--color-primary-400);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.input-sep {
  color: var(--color-neutral-400);
}

.compare-btn {
  padding: var(--space-2) var(--space-5);
  background: var(--gradient-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all 0.2s;
}

.compare-btn:hover {
  opacity: 0.9;
}
</style>