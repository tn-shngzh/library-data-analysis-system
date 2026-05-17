<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { statisticsApi } from '@/api/statistics'
import { formatNumber } from '@/utils/format'
import StatCard from '@/components/StatCard.vue'
import ChartCard from '@/components/ChartCard.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loadingStates = reactive({
  frequency: false,
  descriptive: false,
  crosstab: false,
  clustering: false
})
const loading = computed(() => Object.values(loadingStates).some(v => v))

const errorStates = reactive({
  frequency: null,
  descriptive: null,
  crosstab: null,
  clustering: null
})

const activeTab = ref('frequency')

const frequencyData = ref(null)
const descriptiveData = ref(null)
const crossTabData = ref(null)
const clusteringData = ref(null)

const selectedFrequencyType = ref('book')
const selectedClusterCount = ref(4)

const selectedYear = ref(new Date().getFullYear())
const availableYears = computed(() => {
  const current = new Date().getFullYear()
  return Array.from({ length: 4 }, (_, i) => current - i)
})

const snapshotSaving = reactive({
  frequency: false,
  descriptive: false,
  crosstab: false,
  clustering: false
})

const fetchFrequency = async () => {
  loadingStates.frequency = true
  errorStates.frequency = null
  try {
    frequencyData.value = await statisticsApi.getFrequency(selectedFrequencyType.value, selectedYear.value)
  } catch (e) {
    console.error('Failed to fetch frequency data', e)
    errorStates.frequency = t('stats.loadError')
  } finally {
    loadingStates.frequency = false
  }
}

const fetchDescriptive = async () => {
  loadingStates.descriptive = true
  errorStates.descriptive = null
  try {
    descriptiveData.value = await statisticsApi.getDescriptive('borrows', 'monthly', selectedYear.value)
  } catch (e) {
    console.error('Failed to fetch descriptive data', e)
    errorStates.descriptive = t('stats.loadError')
  } finally {
    loadingStates.descriptive = false
  }
}

const fetchCrossTab = async () => {
  loadingStates.crosstab = true
  errorStates.crosstab = null
  try {
    crossTabData.value = await statisticsApi.getCrossTabulation()
  } catch (e) {
    console.error('Failed to fetch cross tab data', e)
    errorStates.crosstab = t('stats.loadError')
  } finally {
    loadingStates.crosstab = false
  }
}

const fetchClustering = async () => {
  loadingStates.clustering = true
  errorStates.clustering = null
  try {
    clusteringData.value = await statisticsApi.getReaderClustering(selectedClusterCount.value, selectedYear.value)
  } catch (e) {
    console.error('Failed to fetch clustering data', e)
    errorStates.clustering = t('stats.loadError')
  } finally {
    loadingStates.clustering = false
  }
}

const frequencyTypes = computed(() => [
  { id: 'book', label: t('stats.freqBook') },
  { id: 'reader', label: t('stats.freqReader') },
  { id: 'category', label: t('stats.freqCategory') },
  { id: 'action', label: t('stats.freqAction') }
])

const tabs = [
  { id: 'frequency', i18nKey: 'stats.frequency' },
  { id: 'descriptive', i18nKey: 'stats.descriptive' },
  { id: 'crosstab', i18nKey: 'stats.crosstab' },
  { id: 'clustering', i18nKey: 'stats.clustering' }
]

const frequencyTypeColorMap = {
  book: 'var(--data-book)',
  reader: 'var(--data-reader)',
  category: 'var(--data-category)',
  action: 'var(--data-borrow)'
}

const currentFrequencyColor = computed(() => {
  return frequencyTypeColorMap[selectedFrequencyType.value] || 'var(--data-borrow)'
})

const frequencyChartData = computed(() => {
  if (!frequencyData.value?.distribution?.frequencies) return []
  const bins = frequencyData.value.distribution.bins
  const freqs = frequencyData.value.distribution.frequencies
  return bins.map((bin, i) => ({ label: t('stats.borrowCountBin', { n: bin }), value: freqs[i] || 0 }))
})

const maxFrequency = computed(() => {
  if (!frequencyChartData.value.length) return 1
  return Math.max(...frequencyChartData.value.map(d => d.value))
})

const getBarHeight = (value) => {
  return (value / maxFrequency.value) * 100 + '%'
}

const frequencyStats = computed(() => {
  const d = frequencyData.value
  if (!d?.summary) return []
  return [
    { label: t('stats.totalSamples'), value: formatNumber(d.summary.count || d.summary.total) },
    { label: t('stats.mean'), value: formatNumber(d.summary.mean) },
    { label: t('stats.median'), value: formatNumber(d.summary.median) }
  ]
})

const descriptiveStats = computed(() => {
  const d = descriptiveData.value
  if (!d?.stats) return []
  return [
    { label: t('stats.mean'), value: formatNumber(d.stats.mean) },
    { label: t('stats.stdDev'), value: formatNumber(d.stats.std) },
    { label: t('stats.sampleCount'), value: formatNumber(d.stats.count) }
  ]
})

const crosstabStats = computed(() => [])

const clusteringStats = computed(() => {
  const d = clusteringData.value
  if (!d?.summary) return []
  const largestCount = d.clusters?.length
    ? Math.max(...d.clusters.map(c => c.count))
    : 0
  return [
    { label: t('stats.clusterReaders'), value: formatNumber(d.summary.total_readers) },
    { label: t('stats.clusterGroups'), value: String(d.summary.n_clusters) },
    { label: t('stats.largestGroup'), value: formatNumber(largestCount) }
  ]
})

const descriptiveStatCards = computed(() => {
  if (!descriptiveData.value?.stats) return []
  const s = descriptiveData.value.stats
  return [
    { label: t('stats.sampleCount'), value: s.count, color: 'var(--data-borrow)' },
    { label: t('stats.sum'), value: s.sum, color: 'var(--data-borrow)' },
    { label: t('stats.mean'), value: s.mean, color: 'var(--data-reader)' },
    { label: t('stats.stdDev'), value: s.std, color: 'var(--data-reader)' },
    { label: t('stats.min'), value: s.min, color: 'var(--data-return)' },
    { label: t('stats.max'), value: s.max, color: 'var(--data-return)' },
    { label: t('stats.q25'), value: s.q25, color: 'var(--data-book)' },
    { label: t('stats.median'), value: s.median, color: 'var(--data-book)' },
    { label: t('stats.q75'), value: s.q75, color: 'var(--data-category)' },
    { label: t('stats.skewness'), value: s.skewness, color: 'var(--data-category)' },
    { label: t('stats.kurtosis'), value: s.kurtosis, color: 'var(--data-borrow)' }
  ]
})

const maxValue = computed(() => {
  if (!crossTabData.value?.matrix) return 0
  return Math.max(...crossTabData.value.matrix.flat())
})

const getCellColor = (value) => {
  if (!value || maxValue.value === 0) return 'var(--color-neutral-100)'
  const intensity = value / maxValue.value
  return `rgba(59, 130, 246, ${0.2 + intensity * 0.8})`
}

const clusterColors = ['var(--data-reader)', 'var(--data-return)', 'var(--data-borrow)', 'var(--data-book)', 'var(--data-category)', '#8B5CF6', '#EC4899', '#06B6D4']

const saveSnapshot = async (tabKey) => {
  snapshotSaving[tabKey] = true
  try {
    const dataMap = {
      frequency: frequencyData.value,
      descriptive: descriptiveData.value,
      crosstab: crossTabData.value,
      clustering: clusteringData.value
    }
    await statisticsApi.saveSnapshot({
      tab: tabKey,
      data: dataMap[tabKey],
      year: selectedYear.value,
      frequencyType: selectedFrequencyType.value,
      clusterCount: selectedClusterCount.value
    })
  } catch (e) {
    console.error('Failed to save snapshot', e)
  } finally {
    snapshotSaving[tabKey] = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'frequency') fetchFrequency()
  else if (tab === 'descriptive') fetchDescriptive()
  else if (tab === 'crosstab') fetchCrossTab()
  else if (tab === 'clustering') fetchClustering()
})

watch(selectedFrequencyType, () => {
  if (activeTab.value === 'frequency') fetchFrequency()
})

watch(selectedClusterCount, () => {
  if (activeTab.value === 'clustering') fetchClustering()
})

watch(selectedYear, () => {
  if (activeTab.value === 'frequency') fetchFrequency()
  else if (activeTab.value === 'clustering') fetchClustering()
})

onMounted(() => {
  fetchFrequency()
})
</script>

<template>
  <div class="stats-container">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ t('stats.title') }}</h1>
        <p class="page-subtitle">{{ t('stats.desc') }}</p>
      </div>
    </div>

    <div class="tabs-container">
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ t(tab.i18nKey) }}
        </button>
      </div>
    </div>

    <div v-if="activeTab === 'frequency'" class="tab-content">
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">{{ t('stats.yearFilter') }}</label>
          <select v-model="selectedYear" class="select-control">
            <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="filter-group">
          <select v-model="selectedFrequencyType" class="select-control">
            <option v-for="ft in frequencyTypes" :key="ft.id" :value="ft.id">
              {{ ft.label }}
            </option>
          </select>
        </div>
      </div>

      <LoadingSpinner v-if="loadingStates.frequency" />

      <div v-else-if="errorStates.frequency" class="error-state">
        <span class="error-text">{{ errorStates.frequency }}</span>
        <button class="retry-btn" @click="fetchFrequency">{{ t('stats.retry') }}</button>
      </div>

      <div v-else-if="!frequencyData" class="empty-state">
        <span>{{ t('stats.noData') }}</span>
      </div>

      <div v-else-if="frequencyData" class="frequency-section">
        <ChartCard :title="frequencyData.title || t('stats.frequencyAnalysis')" :color="currentFrequencyColor" :stats="frequencyStats">
          <template #actions>
            <button
              class="snapshot-btn"
              :disabled="snapshotSaving.frequency"
              @click="saveSnapshot('frequency')"
            >
              {{ snapshotSaving.frequency ? '...' : t('stats.saveSnapshot') }}
            </button>
          </template>

          <p class="card-desc">{{ frequencyData.description }}</p>

          <div v-if="frequencyData.distribution?.frequencies" class="frequency-chart">
            <div
              v-for="(item, idx) in frequencyChartData.slice(0, 15)"
              :key="idx"
              class="bar-item"
            >
              <div class="bar-wrapper">
                <div
                  class="bar-fill"
                  :style="{ height: getBarHeight(item.value), background: `linear-gradient(180deg, ${currentFrequencyColor} 0%, ${currentFrequencyColor}99 100%)` }"
                >
                  <span class="bar-value">{{ item.value }}</span>
                </div>
              </div>
              <span class="bar-label">{{ item.label }}</span>
            </div>
          </div>

          <div v-if="frequencyData.summary" class="stats-summary">
            <StatCard
              v-if="frequencyData.summary.count || frequencyData.summary.total"
              :label="t('stats.total')"
              :value="frequencyData.summary.count || frequencyData.summary.total"
              :color="currentFrequencyColor"
            />
            <StatCard
              v-if="frequencyData.summary.mean"
              :label="t('stats.mean')"
              :value="frequencyData.summary.mean"
              :color="currentFrequencyColor"
            />
            <StatCard
              v-if="frequencyData.summary.std"
              :label="t('stats.stdDev')"
              :value="frequencyData.summary.std"
              :color="currentFrequencyColor"
            />
            <StatCard
              v-if="frequencyData.summary.median"
              :label="t('stats.median')"
              :value="frequencyData.summary.median"
              :color="currentFrequencyColor"
            />
          </div>
        </ChartCard>
      </div>
    </div>

    <div v-else-if="activeTab === 'descriptive'" class="tab-content">
      <LoadingSpinner v-if="loadingStates.descriptive" />

      <div v-else-if="errorStates.descriptive" class="error-state">
        <span class="error-text">{{ errorStates.descriptive }}</span>
        <button class="retry-btn" @click="fetchDescriptive">{{ t('stats.retry') }}</button>
      </div>

      <div v-else-if="!descriptiveData" class="empty-state">
        <span>{{ t('stats.noData') }}</span>
      </div>

      <div v-else-if="descriptiveData" class="descriptive-section">
        <ChartCard :title="t('stats.borrowDescriptive')" color="var(--data-borrow)" :stats="descriptiveStats">
          <template #actions>
            <button
              class="snapshot-btn"
              :disabled="snapshotSaving.descriptive"
              @click="saveSnapshot('descriptive')"
            >
              {{ snapshotSaving.descriptive ? '...' : t('stats.saveSnapshot') }}
            </button>
          </template>

          <div v-if="descriptiveData.stats" class="descriptive-stats-grid">
            <StatCard
              v-for="(card, idx) in descriptiveStatCards"
              :key="card.label"
              :label="card.label"
              :value="card.value"
              :color="card.color"
              :delay="idx * 0.03"
            />
          </div>

          <div v-if="descriptiveData.data?.length" class="mini-trend-chart">
            <div
              v-for="(item, idx) in descriptiveData.data.slice(0, 30)"
              :key="idx"
              class="trend-bar"
              :style="{ height: (item.value / (descriptiveData.stats?.max || 1) * 100) + '%', background: 'var(--data-borrow)' }"
              :title="`${item.date}: ${item.value}`"
            ></div>
          </div>
        </ChartCard>
      </div>
    </div>

    <div v-else-if="activeTab === 'crosstab'" class="tab-content">
      <LoadingSpinner v-if="loadingStates.crosstab" />

      <div v-else-if="errorStates.crosstab" class="error-state">
        <span class="error-text">{{ errorStates.crosstab }}</span>
        <button class="retry-btn" @click="fetchCrossTab">{{ t('stats.retry') }}</button>
      </div>

      <div v-else-if="!crossTabData" class="empty-state">
        <span>{{ t('stats.noData') }}</span>
      </div>

      <div v-else-if="crossTabData?.matrix?.length" class="crosstab-section">
        <ChartCard :title="t('stats.crosstabTitle')" color="var(--data-category)" :stats="crosstabStats">
          <template #actions>
            <button
              class="snapshot-btn"
              :disabled="snapshotSaving.crosstab"
              @click="saveSnapshot('crosstab')"
            >
              {{ snapshotSaving.crosstab ? '...' : t('stats.saveSnapshot') }}
            </button>
          </template>

          <p class="card-desc">{{ t('stats.crosstabDesc') }}</p>

          <div class="table-wrapper">
            <table class="crosstab-table">
              <thead>
                <tr>
                  <th class="row-header-cell"></th>
                  <th v-for="col in crossTabData.colHeaders" :key="col" class="col-header-cell">
                    {{ col }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIdx) in crossTabData.rowHeaders" :key="row">
                  <td class="row-header-cell">{{ row }}</td>
                  <td
                    v-for="(col, colIdx) in crossTabData.colHeaders"
                    :key="col"
                    class="data-cell"
                    :style="{ backgroundColor: getCellColor(crossTabData.matrix[rowIdx]?.[colIdx]) }"
                  >
                    {{ crossTabData.matrix[rowIdx]?.[colIdx] || 0 }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </ChartCard>
      </div>
    </div>

    <div v-else-if="activeTab === 'clustering'" class="tab-content">
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">{{ t('stats.yearFilter') }}</label>
          <select v-model="selectedYear" class="select-control">
            <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">{{ t('stats.clusterCount') }}</label>
          <select v-model="selectedClusterCount" class="select-control">
            <option v-for="n in [2, 3, 4, 5, 6]" :key="n" :value="n">{{ n }} {{ t('stats.clusterUnit') }}</option>
          </select>
        </div>
      </div>

      <LoadingSpinner v-if="loadingStates.clustering" />

      <div v-else-if="errorStates.clustering" class="error-state">
        <span class="error-text">{{ errorStates.clustering }}</span>
        <button class="retry-btn" @click="fetchClustering">{{ t('stats.retry') }}</button>
      </div>

      <div v-else-if="!clusteringData" class="empty-state">
        <span>{{ t('stats.noData') }}</span>
      </div>

      <div v-else-if="clusteringData?.clusters?.length" class="clustering-section">
        <ChartCard :title="t('stats.clusteringTitle')" color="var(--data-reader)" :stats="clusteringStats">
          <template #actions>
            <button
              class="snapshot-btn"
              :disabled="snapshotSaving.clustering"
              @click="saveSnapshot('clustering')"
            >
              {{ snapshotSaving.clustering ? '...' : t('stats.saveSnapshot') }}
            </button>
          </template>

          <p class="card-desc">{{ t('stats.clusteringDesc') }}</p>

          <div class="clusters-grid">
            <div
              v-for="cluster in clusteringData.clusters"
              :key="cluster.id"
              class="cluster-card"
              :style="{ borderColor: clusterColors[cluster.id % clusterColors.length] }"
            >
              <div class="cluster-header">
                <span
                  class="cluster-badge"
                  :style="{ backgroundColor: clusterColors[cluster.id % clusterColors.length] }"
                ></span>
                <span class="cluster-name">{{ cluster.name }}</span>
              </div>
              <div class="cluster-stats">
                <StatCard :label="t('stats.peopleCount')" :value="cluster.count" color="var(--data-reader)" />
                <StatCard :label="t('stats.percentLabel')" :value="cluster.percent" unit="%" color="var(--data-reader)" />
                <StatCard :label="t('stats.avgBorrowPerReader')" :value="cluster.avg_borrows" :unit="t('stats.timesUnit')" color="var(--data-borrow)" />
                <StatCard :label="t('stats.avgReturnPerReader')" :value="cluster.avg_returns" :unit="t('stats.timesUnit')" color="var(--data-return)" />
                <StatCard :label="t('stats.avgBooksPerReader')" :value="cluster.avg_unique_books" :unit="t('stats.booksUnit')" color="var(--data-book)" />
              </div>
            </div>
          </div>

          <div v-if="clusteringData.summary" class="cluster-summary">
            <span>{{ t('stats.clusterSummary', [formatNumber(clusteringData.summary.total_readers), clusteringData.summary.n_clusters]) }}</span>
          </div>
        </ChartCard>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-4);
  height: calc(100vh - var(--header-height) - 48px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.page-header {
  flex-shrink: 0;
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  margin: 0;
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: var(--space-1) 0 0;
}

.tabs-container {
  flex-shrink: 0;
}

.tabs {
  display: flex;
  gap: var(--space-1);
  background: var(--color-neutral-100);
  padding: 4px;
  border-radius: var(--radius-lg);
  overflow-x: auto;
}

.tab {
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-600);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab:hover {
  color: var(--color-neutral-800);
}

.tab.active {
  background: white;
  color: var(--color-primary-600);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.filter-label {
  font-size: var(--text-sm);
  color: var(--color-neutral-600);
  white-space: nowrap;
}

.select-control {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  background: white;
  font-size: var(--text-sm);
}

.quick-periods {
  display: flex;
  gap: var(--space-1);
}

.period-btn {
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  background: white;
  font-size: var(--text-sm);
  color: var(--color-neutral-600);
  cursor: pointer;
  transition: all 0.2s;
}

.period-btn:hover {
  border-color: var(--color-primary-300);
  color: var(--color-primary-600);
}

.period-btn.active {
  background: var(--color-primary-600);
  border-color: var(--color-primary-600);
  color: white;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  flex: 1;
  min-height: 0;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
}

.error-text {
  font-size: var(--text-sm);
  color: var(--color-danger-500);
}

.retry-btn {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  background: white;
  font-size: var(--text-sm);
  color: var(--color-primary-600);
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: var(--color-primary-50);
  border-color: var(--color-primary-300);
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-8);
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
}

.snapshot-btn {
  padding: var(--space-1) var(--space-3);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  background: white;
  font-size: var(--text-xs);
  color: var(--color-neutral-600);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.snapshot-btn:hover:not(:disabled) {
  background: var(--color-primary-50);
  border-color: var(--color-primary-300);
  color: var(--color-primary-600);
}

.snapshot-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.card-desc {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0 0 var(--space-4);
}

.frequency-chart {
  display: flex;
  align-items: flex-end;
  gap: var(--space-2);
  height: 200px;
  padding: var(--space-4) 0;
}

.bar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.bar-fill {
  width: 80%;
  max-width: 40px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  transition: height 0.3s ease;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 4px;
}

.bar-value {
  font-size: 10px;
  color: white;
  padding: 2px;
  font-weight: var(--font-semibold);
}

.bar-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  margin-top: var(--space-2);
  text-align: center;
}

.stats-summary {
  display: flex;
  gap: var(--space-4);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-neutral-100);
  flex-wrap: wrap;
}

.stats-summary :deep(.stat-card) {
  min-height: auto;
  padding: var(--space-3);
}

.descriptive-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.descriptive-stats-grid :deep(.stat-card) {
  min-height: auto;
  padding: var(--space-3);
}

.mini-trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 60px;
}

.trend-bar {
  flex: 1;
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height 0.2s ease;
}

.table-wrapper {
  overflow-x: auto;
}

.crosstab-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-xs);
}

.crosstab-table th,
.crosstab-table td {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-neutral-200);
  text-align: center;
}

.row-header-cell {
  background: var(--color-neutral-50);
  font-weight: var(--font-medium);
  text-align: left !important;
}

.col-header-cell {
  background: var(--color-neutral-50);
  font-weight: var(--font-medium);
}

.data-cell {
  transition: background-color 0.2s ease;
}

.clusters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.cluster-card {
  border: 2px solid;
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: white;
}

.cluster-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.cluster-badge {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.cluster-name {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.cluster-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.cluster-stats :deep(.stat-card) {
  min-height: auto;
  padding: var(--space-2) var(--space-3);
}

.cluster-summary {
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-neutral-100);
}

@media (max-width: 768px) {
  .filter-bar {
    flex-wrap: wrap;
  }
}
</style>
