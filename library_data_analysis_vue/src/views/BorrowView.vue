<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { borrowApi } from '@/api/borrows'
import { ACTION_MAP, ACTION_COLORS, DEGREE_MAP } from '@/constants'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const borrowStats = ref({
  total_actions: 0,
  total_borrows: 0,
  total_returns: 0,
  total_renewals: 0,
  active_borrowers: 0,
  borrowed_books: 0
})

const actionStats = ref([])
const degreeStats = ref([])
const topBorrowers = ref([])
const topBooks = ref([])
const recentBorrows = ref([])
const loading = ref(true)

const actionMap = ACTION_MAP
const actionColors = ACTION_COLORS
const degreeMap = DEGREE_MAP
const borrowColor = 'var(--data-borrow)'

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const actionStats_header = computed(() => [
  { label: t('borrow.totalActions'), value: formatNumber(borrowStats.value.total_actions) },
  { label: t('borrow.totalBorrows'), value: formatNumber(borrowStats.value.total_borrows) }
])
const degreeStats_header = computed(() => [
  { label: t('borrow.totalReturns'), value: formatNumber(borrowStats.value.total_returns) },
  { label: t('borrow.totalRenewals'), value: formatNumber(borrowStats.value.total_renewals) }
])
const topBorrowerStats = computed(() => [
  { label: t('borrow.activeBorrowers'), value: formatNumber(borrowStats.value.active_borrowers) }
])
const topBookStats = computed(() => [
  { label: t('borrow.borrowedBooks'), value: formatNumber(borrowStats.value.borrowed_books) }
])

const fetchBorrowData = async () => {
  loading.value = true
  try {
    const data = await borrowApi.getAll()
    if (data.stats) borrowStats.value = data.stats
    if (data.actionStats) actionStats.value = data.actionStats
    if (data.degreeStats) degreeStats.value = data.degreeStats
    if (data.topBorrowers) topBorrowers.value = data.topBorrowers
    if (data.topBooks) topBooks.value = data.topBooks
    if (data.recentBorrows) recentBorrows.value = data.recentBorrows
  } catch (e) {
    console.error('Failed to fetch borrow data', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.allData?.borrows, (data) => {
  if (data && data.stats) {
    borrowStats.value = data.stats
    actionStats.value = data.actionStats || []
    degreeStats.value = data.degreeStats || []
    topBorrowers.value = data.topBorrowers || []
    topBooks.value = data.topBooks || []
    recentBorrows.value = data.recentBorrows || []
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (!props.allData?.borrows || !props.allData.borrows.stats) {
    fetchBorrowData()
  }
})

const actionPieOption = computed(() => {
  if (!actionStats.value.length) return {}
  const filtered = actionStats.value.filter(i => i.count > 0)
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, left: 'center', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      data: filtered.map(item => ({
        name: item.name,
        value: item.count,
        itemStyle: { color: actionColors[item.action] }
      }))
    }]
  }
})

const degreeBarOption = computed(() => {
  if (!degreeStats.value.length) return {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: degreeStats.value.map(d => d.name), axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value', name: t('borrow.count') },
    series: [{
      type: 'bar',
      data: degreeStats.value.map(d => d.count),
      itemStyle: { borderRadius: [4, 4, 0, 0], color: '#d97706' },
      barWidth: '50%'
    }]
  }
})

const topBorrowerBarOption = computed(() => {
  if (!topBorrowers.value.length) return {}
  const data = topBorrowers.value.slice(0, 10)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: t('borrow.count') },
    yAxis: {
      type: 'category',
      data: data.map(b => String(b.borrower_id)).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: data.map(b => b.borrow_count).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#d97706' },
      barWidth: '60%'
    }]
  }
})

const topBookBarOption = computed(() => {
  if (!topBooks.value.length) return {}
  const data = topBooks.value.slice(0, 10)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: t('borrow.count') },
    yAxis: {
      type: 'category',
      data: data.map(b => String(b.bib_id)).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: data.map(b => b.borrow_count).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#d97706' },
      barWidth: '60%'
    }]
  }
})
</script>

<template>
  <div class="borrows">
    <PageHeader :title="t('borrow.title')" :description="t('borrow.desc')" :loading="loading" @refresh="fetchBorrowData" />

    <LoadingSpinner :loading="loading">
      <div class="dashboard-row">
        <div class="dashboard-col">
          <ChartCard :title="t('borrow.actionStats')" :color="borrowColor" :stats="actionStats_header">
            <div class="chart-container">
              <v-chart class="chart" :option="actionPieOption" autoresize />
            </div>
          </ChartCard>
        </div>
        <div class="dashboard-col">
          <ChartCard :title="t('borrow.degreeStats')" :color="borrowColor" :stats="degreeStats_header">
            <div class="chart-container">
              <v-chart class="chart" :option="degreeBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
      </div>

      <div class="dashboard-row">
        <div class="dashboard-col">
          <ChartCard :title="t('borrow.topBorrowers')" :color="borrowColor" :stats="topBorrowerStats">
            <div class="chart-container">
              <v-chart class="chart" :option="topBorrowerBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
        <div class="dashboard-col">
          <ChartCard :title="t('borrow.topBooks')" :color="borrowColor" :stats="topBookStats">
            <div class="chart-container">
              <v-chart class="chart" :option="topBookBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.borrows {
  max-width: var(--main-max-width);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.dashboard-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.dashboard-row :deep(.chart-card) {
  height: 100%;
}

.dashboard-col {
  min-width: 0;
  min-height: 0;
}

.chart-container {
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 240px;
}

@media (max-width: 1024px) {
  .dashboard-row {
    grid-template-columns: 1fr;
  }
}
</style>
