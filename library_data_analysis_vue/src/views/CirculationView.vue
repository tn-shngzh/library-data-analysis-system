<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { borrowApi } from '@/api/borrows'
import { readerApi } from '@/api/readers'
import { formatNumber } from '@/utils/format'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'

const { t } = useI18n()

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (v) => ['borrow', 'reader'].includes(v)
  },
  allData: {
    type: Object,
    default: null
  }
})

const isBorrow = computed(() => props.type === 'borrow')

const stats = ref({})
const degreeStats = ref([])
const actionStats = ref([])
const readerTypes = ref([])
const frequencyDistribution = ref({ groups: [], details: {} })
const topBooks = ref([])
const topReaders = ref([])
const recentBorrows = ref([])
const degreeHourHeatmap = ref({ degrees: [], hours: [], data: [], max: 0 })
const loading = ref(true)

const borrowStats = computed(() => isBorrow.value ? stats.value : {})
const readerStats = computed(() => !isBorrow.value ? stats.value : {})

const borrowActionStats = computed(() => [
  { label: t('borrow.totalActions'), value: formatNumber(borrowStats.value.total_actions) },
  { label: t('borrow.totalBorrows'), value: formatNumber(borrowStats.value.total_borrows) }
])
const borrowDegreeStats = computed(() => [
  { label: t('borrow.totalReturns'), value: formatNumber(borrowStats.value.total_returns) },
  { label: t('borrow.totalRenewals'), value: formatNumber(borrowStats.value.total_renewals) }
])
const borrowTopBookStats = computed(() => [
  { label: t('borrow.activeBorrowers'), value: formatNumber(borrowStats.value.active_borrowers) }
])
const borrowRecentStats = computed(() => [
  { label: t('borrow.borrowedBooks'), value: formatNumber(borrowStats.value.borrowed_books) }
])

const readerDistStats = computed(() => [
  { label: t('reader.totalReaders'), value: formatNumber(readerStats.value.total_readers) }
])
const readerFreqStats = computed(() => [
  { label: t('reader.monthActive'), value: formatNumber(readerStats.value.month_active) }
])
const readerTopStats = computed(() => [
  { label: t('reader.monthNew'), value: formatNumber(readerStats.value.month_new) }
])
const readerHeatmapStats = computed(() => [
  { label: t('reader.avgBorrows'), value: String(readerStats.value.avg_borrows) }
])

const pageTitle = computed(() => isBorrow.value ? t('borrow.title') : t('reader.title'))
const pageDesc = computed(() => isBorrow.value ? t('borrow.desc') : t('reader.desc'))

async function fetchBorrowData() {
  loading.value = true
  try {
    const data = await borrowApi.getAll()
    if (data.stats) stats.value = data.stats
    if (data.degreeStats) degreeStats.value = data.degreeStats
    if (data.actionStats) actionStats.value = data.actionStats
    if (data.topBooks) topBooks.value = data.topBooks
    if (data.recentBorrows) recentBorrows.value = data.recentBorrows
  } catch (e) {
    console.error('Failed to fetch borrow data', e)
  } finally {
    loading.value = false
  }
}

async function fetchReaderData() {
  loading.value = true
  try {
    const data = await readerApi.getAll()
    if (data.stats) stats.value = data.stats
    if (data.degreeStats) degreeStats.value = data.degreeStats
    if (data.readerTypes) readerTypes.value = data.readerTypes
    if (data.topReaders) topReaders.value = data.topReaders
    if (data.frequencyDistribution) frequencyDistribution.value = data.frequencyDistribution
    if (data.degreeHourHeatmap) degreeHourHeatmap.value = data.degreeHourHeatmap
  } catch (e) {
    console.error('Failed to fetch reader data', e)
  } finally {
    loading.value = false
  }
}

function applyAllData() {
  if (!props.allData) return
  if (isBorrow.value && props.allData.borrows?.stats) {
    const d = props.allData.borrows
    stats.value = d.stats
    degreeStats.value = d.degreeStats || []
    actionStats.value = d.actionStats || []
    topBooks.value = d.topBooks || []
    recentBorrows.value = d.recentBorrows || []
    loading.value = false
  } else if (!isBorrow.value && props.allData.readers?.stats) {
    const d = props.allData.readers
    stats.value = d.stats
    degreeStats.value = d.degreeStats || []
    readerTypes.value = d.readerTypes || []
    topReaders.value = d.topReaders || []
    frequencyDistribution.value = d.frequencyDistribution || { groups: [], details: {} }
    degreeHourHeatmap.value = d.degreeHourHeatmap || { degrees: [], hours: [], data: [], max: 0 }
    loading.value = false
  }
}

watch(() => props.type, () => {
  applyAllData()
  if (loading.value) {
    isBorrow.value ? fetchBorrowData() : fetchReaderData()
  }
})

onMounted(() => {
  applyAllData()
  if (loading.value) {
    isBorrow.value ? fetchBorrowData() : fetchReaderData()
  }
})

const fetchData = () => isBorrow.value ? fetchBorrowData() : fetchReaderData()

const degreeBarOption = computed(() => {
  if (!degreeStats.value.length) return {}
  const isBorrowMode = isBorrow.value
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: degreeStats.value.map(d => d.degree_name || d.name),
      axisLabel: { rotate: 35, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: isBorrowMode ? t('borrow.count') : t('reader.personCount')
    },
    series: [{
      type: 'bar',
      data: degreeStats.value.map(d => d.count),
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: isBorrowMode ? '#d97706' : '#6366f1'
      },
      barWidth: '50%'
    }]
  }
})

const distPieOption = computed(() => {
  if (isBorrow.value) {
    if (!actionStats.value.length) return {}
    const filtered = actionStats.value.filter(i => i.count > 0)
    return {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, left: 'center', textStyle: { fontSize: 11 } },
      series: [{
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
        data: filtered.map(item => ({
          name: item.name,
          value: item.count,
          itemStyle: { color: item.color }
        }))
      }]
    }
  } else {
    const groups = frequencyDistribution.value.groups
    if (!groups.length) return {}
    const colors = ['#f59e0b', '#6366f1', '#94a3b8']
    return {
      tooltip: {
        trigger: 'item',
        formatter: (p) => `${p.name}: ${p.value}人 (${p.percent}%)<br/>阈值: ${groups[p.dataIndex].threshold}`
      },
      legend: { bottom: 0, left: 'center', textStyle: { fontSize: 11 } },
      series: [{
        type: 'pie',
        radius: ['45%', '72%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
        data: groups.map((g, i) => ({
          name: g.name,
          value: g.count,
          itemStyle: { color: colors[i] }
        }))
      }]
    }
  }
})

const topRankingItems = computed(() => {
  if (isBorrow.value) {
    return topBooks.value.map(b => ({
      rank: b.rank,
      name: b.bib_id,
      value: b.borrow_count,
      meta: b.category
    }))
  }
  return topReaders.value.map(r => ({
    rank: r.rank,
    name: r.id,
    value: r.borrowed,
    meta: r.type
  }))
})

const topBarOption = computed(() => {
  const items = topRankingItems.value
  if (!items.length) return {}
  const data = items.slice(0, 10)
  const color = isBorrow.value ? '#d97706' : '#ef4444'
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: data.map(d => String(d.name)).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.value).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color },
      barWidth: '60%'
    }]
  }
})

const heatmapOption = computed(() => {
  const hm = degreeHourHeatmap.value
  if (!hm.degrees || !hm.degrees.length) return {}
  return {
    tooltip: {
      position: 'top',
      formatter: (p) => `${hm.degrees[p.value[1]]} ${hm.hours[p.value[0]]}: ${p.value[2]}次`
    },
    grid: { left: '15%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: hm.hours,
      splitArea: { show: true },
      axisLabel: { fontSize: 10, interval: 1 }
    },
    yAxis: {
      type: 'category',
      data: hm.degrees,
      splitArea: { show: true },
      axisLabel: { fontSize: 11 }
    },
    visualMap: {
      min: 0,
      max: hm.max || 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      itemWidth: 12,
      itemHeight: 80,
      inRange: { color: ['#f0f5ff', '#dbeafe', '#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af'] }
    },
    series: [{
      type: 'heatmap',
      data: hm.data,
      label: { show: false },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } }
    }]
  }
})

const distPieTitle = computed(() =>
  isBorrow.value ? t('borrow.actionStats') : t('reader.frequencyDistribution')
)

const topRankingTitle = computed(() =>
  isBorrow.value ? t('borrow.topBooks') : t('reader.topReaders')
)

const degreeBarTitle = computed(() =>
  isBorrow.value ? t('borrow.degreeStats') : t('reader.degreeTab')
)

const topColor = computed(() =>
  isBorrow.value ? 'var(--color-warning-500)' : 'var(--color-danger-500)'
)
</script>

<template>
  <div class="circulation">
    <PageHeader :title="pageTitle" :description="pageDesc" :loading="loading" @refresh="fetchData" />

    <LoadingSpinner :loading="loading">
      <div class="dashboard-row">
        <div class="dashboard-col">
          <ChartCard :title="degreeBarTitle" :color="isBorrow ? 'var(--data-borrow)' : 'var(--color-primary-500)'" :delay="0.2" :stats="isBorrow ? borrowDegreeStats : readerDistStats">
            <div class="chart-container">
              <v-chart class="chart" :option="degreeBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
        <div class="dashboard-col">
          <ChartCard :title="distPieTitle" :color="isBorrow ? 'var(--color-warning-500)' : 'var(--color-warning-500)'" :delay="0.3" :stats="isBorrow ? borrowActionStats : readerFreqStats">
            <div class="chart-container">
              <v-chart class="chart" :option="distPieOption" autoresize />
            </div>
            <div v-if="!isBorrow && frequencyDistribution.details.total_readers" class="freq-details">
              <div class="freq-detail-item">
                <span class="freq-label">{{ t('reader.totalReadersLabel') }}</span>
                <span class="freq-value">{{ frequencyDistribution.details.total_readers }}</span>
              </div>
              <div class="freq-detail-item">
                <span class="freq-label">{{ t('reader.avgBorrowsLabel') }}</span>
                <span class="freq-value">{{ frequencyDistribution.details.avg_borrows }}</span>
              </div>
            </div>
          </ChartCard>
        </div>
      </div>

      <div class="dashboard-row">
        <div class="dashboard-col">
          <ChartCard :title="topRankingTitle" :color="topColor" :delay="0.4" :stats="isBorrow ? borrowTopBookStats : readerTopStats">
            <div class="chart-container top-chart-container">
              <v-chart class="chart" :option="topBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
        <div class="dashboard-col">
          <ChartCard
            v-if="isBorrow"
            :title="t('borrow.recentBorrows')"
            :color="'var(--color-success-500)'"
            :delay="0.5"
            :stats="borrowRecentStats"
          >
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ t('borrow.date') }}</th>
                  <th>{{ t('borrow.readerId') }}</th>
                  <th>{{ t('borrow.bookId') }}</th>
                  <th>{{ t('borrow.type') }}</th>
                  <th>{{ t('borrow.category') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in recentBorrows" :key="index" class="table-row" :style="{ '--delay': index * 0.03 + 's' }">
                  <td>{{ item.date }}</td>
                  <td class="id-cell">{{ item.borrower_id }}</td>
                  <td class="id-cell">{{ item.bib_id }}</td>
                  <td><span class="type-tag">{{ item.degree }}</span></td>
                  <td><span class="category-tag">{{ item.category }}</span></td>
                </tr>
                <tr v-if="recentBorrows.length === 0" class="empty-row">
                  <td colspan="5">{{ t('common.noData') }}</td>
                </tr>
              </tbody>
            </table>
          </ChartCard>
          <ChartCard
            v-else
            :title="t('reader.degreeHourHeatmap')"
            :color="'var(--color-success-500)'"
            :delay="0.5"
            :stats="readerHeatmapStats"
          >
            <div class="chart-container heatmap-container">
              <v-chart class="chart heatmap-chart" :option="heatmapOption" autoresize />
            </div>
          </ChartCard>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.circulation {
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

.freq-details {
  display: flex;
  gap: var(--space-6);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-neutral-100);
}

.freq-detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.freq-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.freq-value {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-primary-600);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-500);
  border-bottom: 2px solid var(--color-neutral-200);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.data-table td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
  border-bottom: 1px solid var(--color-neutral-100);
  transition: background var(--transition-fast);
}

.data-table tbody tr:hover td {
  background: var(--color-neutral-50);
}

.table-row {
  animation: fadeIn 0.3s ease backwards;
  animation-delay: var(--delay);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.type-tag {
  font-size: var(--text-xs);
  color: var(--color-primary-600);
  background: var(--color-primary-50);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-weight: var(--font-medium);
  white-space: nowrap;
}

.category-tag {
  font-size: var(--text-xs);
  color: var(--color-success-600);
  background: var(--color-success-50);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-weight: var(--font-medium);
  white-space: nowrap;
}

.id-cell {
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.empty-row td {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
}

@media (max-width: 1024px) {
  .dashboard-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .freq-details {
    flex-direction: column;
    gap: var(--space-3);
  }
}
</style>