<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAnalysisStore } from '@/stores/analysis'
import { borrowApi } from '@/api/borrows'
import { readerApi } from '@/api/readers'
import TrendChart from '@/components/TrendChart.vue'
import PieChart from '@/components/PieChart.vue'
import RankingCard from '@/components/RankingCard.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const { t } = useI18n()
const analysisStore = useAnalysisStore()

const activeView = ref('borrow')
const loading = ref(true)
let isLoading = false

const borrowTrend = ref([])
const borrowDist = ref([])
const actionTypeStats = ref([])
const topBooks = ref([])

const readerTrend = ref([])
const readerDist = ref([])
const readerTypeStats = ref([])
const topReaders = ref([])

const dateRange = ref({ start: '', end: '' })

const chartColors = {
  borrow: '#d97706',
  reader: '#3b82f6',
  action: ['#1677ff', '#52c41a', '#faad14', '#722ed1', '#13c2c2', '#eb2f96'],
  category: ['#1677ff', '#52c41a', '#faad14', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16', '#ec4899']
}

const currentColor = computed(() => activeView.value === 'borrow' ? chartColors.borrow : chartColors.reader)
const currentDist = computed(() => activeView.value === 'borrow' ? borrowDist.value : readerDist.value)
const currentTop = computed(() => activeView.value === 'borrow' ? topBooks.value : topReaders.value)
const currentTypeStats = computed(() => activeView.value === 'borrow' ? actionTypeStats.value : readerTypeStats.value)

const fetchBorrowData = async () => {
  loading.value = true
  try {
    const params = analysisStore.globalDateRange.start ?
      `?start_date=${analysisStore.globalDateRange.start}&end_date=${analysisStore.globalDateRange.end}` : ''

    const [trendData, actionData, degreeData, booksData] = await Promise.all([
      borrowApi.getDailyTrend(params),
      borrowApi.getActionStats(params),
      borrowApi.getDegreeStats(params),
      borrowApi.getTopBooks(params)
    ])

    borrowTrend.value = Array.isArray(trendData) ? trendData.map(d => ({ value: d.count || 0, label: d.date || '' })) : []
    actionTypeStats.value = Array.isArray(actionData) ? actionData.map(a => ({ name: a.name || a.action, value: a.count || a.value || 0, percent: a.percent || 0, color: a.color || '' })) : []
    borrowDist.value = Array.isArray(degreeData) ? degreeData.map(d => ({ name: d.name, value: d.count || d.value || 0 })) : []
    topBooks.value = Array.isArray(booksData) ? booksData.slice(0, 10).map((b, i) => ({
      rank: i + 1,
      name: b.name || b.bib_id || '未知',
      meta: b.category || '',
      value: b.borrow_count || b.count || 0
    })) : []
  } catch (e) {
    console.error('Failed to fetch borrow data', e)
  }
}

const fetchReaderData = async () => {
  loading.value = true
  try {
    const params = analysisStore.globalDateRange.start ?
      `?start_date=${analysisStore.globalDateRange.start}&end_date=${analysisStore.globalDateRange.end}` : ''

    const [trendData, typesData, topData] = await Promise.all([
      readerApi.getMonthlyTrend(params),
      readerApi.getTypes(params),
      readerApi.getTop(params)
    ])

    readerTrend.value = Array.isArray(trendData) ? trendData.map(d => ({ value: d.value || 0, label: d.label || '' })) : []
    readerTypeStats.value = Array.isArray(typesData) ? typesData.map(t => ({ name: t.name, value: t.value || 0, percent: t.percent || 0 })) : []
    topReaders.value = Array.isArray(topData) ? topData.slice(0, 10).map((r, i) => ({
      rank: i + 1,
      name: `读者 ${r.id}`,
      meta: r.type || '',
      value: r.borrowed || 0
    })) : []
    readerDist.value = readerTypeStats.value.slice(0, 7).map(t => ({ name: t.name, value: t.value || 0 }))
  } catch (e) {
    console.error('Failed to fetch reader data', e)
  }
}

const loadData = async () => {
  if (isLoading) return
  isLoading = true
  try {
    if (activeView.value === 'borrow') {
      await fetchBorrowData()
    } else {
      await fetchReaderData()
    }
  } finally {
    isLoading = false
    loading.value = false
  }
}

watch(activeView, () => loadData())
watch(() => analysisStore.globalDateRange, () => loadData())
onMounted(() => loadData())
</script>

<template>
  <div class="trend-view">
    <div class="page-header">
      <h2>{{ t('trend.title') }}</h2>
      <div class="pill-tabs">
        <button
          class="pill-tab"
          :class="{ active: activeView === 'borrow' }"
          @click="activeView = 'borrow'"
        >
          {{ t('trend.borrowTrend') }}
        </button>
        <button
          class="pill-tab"
          :class="{ active: activeView === 'reader' }"
          @click="activeView = 'reader'"
        >
          {{ t('trend.readerTrend') }}
        </button>
      </div>
    </div>

    <LoadingSpinner :loading="loading">
      <div class="charts-grid">
        <div class="chart-section">
          <div class="section-title">
            <span class="title-text">{{ activeView === 'borrow' ? t('trend.borrowTrend') : t('trend.readerTrend') }}</span>
            <span class="title-count">{{ (activeView === 'borrow' ? borrowTrend : readerTrend).length }} 条数据</span>
          </div>
          <div class="chart-card">
            <TrendChart 
              :data="activeView === 'borrow' ? borrowTrend : readerTrend" 
              :color="currentColor" 
              chart-type="line"
            />
          </div>
        </div>

        <div class="chart-section">
          <div class="section-title">
            <span class="title-text">{{ activeView === 'borrow' ? t('trend.actionType') : t('trend.readerType') }}</span>
          </div>
          <div class="chart-card">
            <PieChart 
              :data="currentTypeStats" 
              :colors="chartColors.action"
            />
          </div>
        </div>

        <div class="chart-section">
          <div class="section-title">
            <span class="title-text">{{ activeView === 'borrow' ? t('trend.borrowDist') : t('trend.readerDist') }}</span>
            <span class="title-count">{{ currentDist.length }} 条数据</span>
          </div>
          <div class="chart-card">
            <TrendChart 
              :data="currentDist" 
              :color="currentColor" 
              chart-type="bar"
            />
          </div>
        </div>

        <div class="chart-section">
          <div class="section-title">
            <span class="title-text">{{ activeView === 'borrow' ? t('trend.hotBooks') : t('trend.topReaders') }}</span>
          </div>
          <div class="chart-card ranking-card-wrapper">
            <RankingCard 
              :items="currentTop" 
              :color="currentColor"
            />
          </div>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.trend-view {
  max-width: var(--main-max-width);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  margin: 0;
}

.pill-tabs {
  display: flex;
  gap: 4px;
  background: var(--color-neutral-100);
  padding: 4px;
  border-radius: var(--radius-lg);
}

.pill-tab {
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
  cursor: pointer;
  transition: all 0.2s;
}

.pill-tab.active {
  background: var(--color-neutral-0);
  color: var(--color-neutral-900);
  box-shadow: var(--shadow-sm);
}

.pill-tab:hover:not(.active) {
  color: var(--color-neutral-700);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.chart-section {
  background: var(--chart-bg);
  border-radius: var(--radius-xl);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
  flex-shrink: 0;
}

.title-text {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.title-count {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
}

.chart-card {
  flex: 1;
  min-height: 0;
}

.ranking-card-wrapper {
  min-height: 0;
}

@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
