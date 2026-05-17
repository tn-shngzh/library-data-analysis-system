<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { readerApi } from '@/api/readers'
import { formatNumber } from '@/utils/format'
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

const readerStats = ref({
  total_readers: 0,
  month_active: 0,
  month_new: 0,
  avg_borrows: 0
})

const readerTypes = ref([])
const monthlyTrend = ref([])
const topReaders = ref([])
const degreeStats = ref([])
const degreeHourHeatmap = ref({ degrees: [], hours: [], data: [], max: 0 })
const frequencyDistribution = ref({ groups: [], details: {} })
const loading = ref(true)

const activeTab = ref('type')

const fetchReaderData = async () => {
  loading.value = true
  try {
    const data = await readerApi.getAll()
    if (data.stats) readerStats.value = data.stats
    if (data.readerTypes) readerTypes.value = data.readerTypes
    if (data.monthlyTrend) monthlyTrend.value = data.monthlyTrend
    if (data.topReaders) topReaders.value = data.topReaders
    if (data.degreeStats) degreeStats.value = data.degreeStats
    if (data.degreeHourHeatmap) degreeHourHeatmap.value = data.degreeHourHeatmap
    if (data.frequencyDistribution) frequencyDistribution.value = data.frequencyDistribution
  } catch (e) {
    console.error('Failed to fetch reader data', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.allData?.readers, (data) => {
  if (data && data.stats) {
    readerStats.value = data.stats
    readerTypes.value = data.readerTypes || []
    monthlyTrend.value = data.monthlyTrend || []
    topReaders.value = data.topReaders || []
    degreeStats.value = data.degreeStats || []
    degreeHourHeatmap.value = data.degreeHourHeatmap || { degrees: [], hours: [], data: [], max: 0 }
    frequencyDistribution.value = data.frequencyDistribution || { groups: [], details: {} }
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (!props.allData?.readers || !props.allData.readers.stats) {
    fetchReaderData()
  }
})

const distributionStats = computed(() => [
  { label: t('reader.totalReaders'), value: formatNumber(readerStats.value.total_readers) }
])
const frequencyStats = computed(() => [
  { label: t('reader.monthActive'), value: formatNumber(readerStats.value.month_active) }
])
const heatmapStats = computed(() => [
  { label: t('reader.monthNew'), value: formatNumber(readerStats.value.month_new) }
])
const topReaderStats = computed(() => [
  { label: t('reader.avgBorrows'), value: String(readerStats.value.avg_borrows) }
])

const typePieOption = computed(() => {
  if (!readerTypes.value.length) return {}
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
      emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
      data: readerTypes.value.map(t => ({ name: t.name, value: t.value }))
    }]
  }
})

const degreeBarOption = computed(() => {
  if (!degreeStats.value.length) return {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: degreeStats.value.map(d => d.degree_name), axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value', name: t('reader.personCount') },
    series: [{
      type: 'bar',
      data: degreeStats.value.map(d => d.count),
      itemStyle: { borderRadius: [4, 4, 0, 0], color: '#6366f1' },
      barWidth: '50%'
    }]
  }
})

const heatmapOption = computed(() => {
  const hm = degreeHourHeatmap.value
  if (!hm.degrees.length) return {}
  return {
    tooltip: { position: 'top', formatter: (p) => `${hm.degrees[p.value[1]]} ${hm.hours[p.value[0]]}: ${p.value[2]}次` },
    grid: { left: '15%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: { type: 'category', data: hm.hours, splitArea: { show: true }, axisLabel: { fontSize: 10, interval: 1 } },
    yAxis: { type: 'category', data: hm.degrees, splitArea: { show: true }, axisLabel: { fontSize: 11 } },
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

const freqPieOption = computed(() => {
  const groups = frequencyDistribution.value.groups
  if (!groups.length) return {}
  const colors = ['#f59e0b', '#6366f1', '#94a3b8']
  return {
    tooltip: { trigger: 'item', formatter: (p) => `${p.name}: ${p.value}人 (${p.percent}%)<br/>阈值: ${groups[p.dataIndex].threshold}` },
    legend: { bottom: 0, left: 'center', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      data: groups.map((g, i) => ({ name: g.name, value: g.count, itemStyle: { color: colors[i] } }))
    }]
  }
})

const topReaderBarOption = computed(() => {
  if (!topReaders.value.length) return {}
  const data = topReaders.value.slice(0, 10)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: t('reader.borrowCount') },
    yAxis: {
      type: 'category',
      data: data.map(r => String(r.id)).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: data.map(r => r.borrowed).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#ef4444' },
      barWidth: '60%'
    }]
  }
})
</script>

<template>
  <div class="readers">
    <PageHeader :title="t('reader.title')" :description="t('reader.desc')" :loading="loading" @refresh="fetchReaderData" />

    <LoadingSpinner :loading="loading">
      <div class="dashboard-row">
        <div class="dashboard-col">
          <ChartCard :title="t('reader.distribution')" color="var(--color-primary-500)" :delay="0.2" :stats="distributionStats">
            <template #actions>
              <div class="tab-switch">
                <button class="tab-btn" :class="{ active: activeTab === 'type' }" @click="activeTab = 'type'">{{ t('reader.typeTab') }}</button>
                <button class="tab-btn" :class="{ active: activeTab === 'degree' }" @click="activeTab = 'degree'">{{ t('reader.degreeTab') }}</button>
              </div>
            </template>
            <div class="chart-container">
              <v-chart v-if="activeTab === 'type'" class="chart" :option="typePieOption" autoresize />
              <v-chart v-else class="chart" :option="degreeBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
        <div class="dashboard-col">
          <ChartCard :title="t('reader.frequencyDistribution')" color="var(--color-warning-500)" :delay="0.3" :stats="frequencyStats">
            <div class="chart-container">
              <v-chart class="chart" :option="freqPieOption" autoresize />
            </div>
            <div v-if="frequencyDistribution.details.total_readers" class="freq-details">
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
          <ChartCard :title="t('reader.degreeHourHeatmap')" color="var(--color-success-500)" :delay="0.4" :stats="heatmapStats">
            <div class="chart-container heatmap-container">
              <v-chart class="chart heatmap-chart" :option="heatmapOption" autoresize />
            </div>
          </ChartCard>
        </div>
        <div class="dashboard-col">
          <ChartCard :title="t('reader.topReaders')" color="var(--color-danger-500)" :delay="0.5" :stats="topReaderStats">
            <div class="chart-container">
              <v-chart class="chart" :option="topReaderBarOption" autoresize />
            </div>
          </ChartCard>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.readers {
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

.tab-switch {
  display: flex;
  gap: 4px;
  background: var(--color-neutral-100);
  padding: 4px;
  border-radius: var(--radius-lg);
}

.tab-btn {
  padding: var(--space-1) var(--space-3);
  border: none;
  background: transparent;
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-neutral-700);
}

.tab-btn.active {
  background: var(--color-neutral-0);
  color: var(--color-primary-600);
  box-shadow: var(--shadow-sm);
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
