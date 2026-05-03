<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { analysisApi } from '@/api/analysis'
import { formatNumber } from '@/utils/format'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(false)
const activeTab = ref('correlation')
const correlationData = ref({ reader_type_borrow: [], action_distribution: [] })
const comparisonData = ref({ period1: {}, period2: {}, changes: {} })
const heatmapData = ref({ categories: [], months: [], values: [] })

const period1Start = ref('')
const period1End = ref('')
const period2Start = ref('')
const period2End = ref('')

const fetchCorrelation = async () => {
  loading.value = true
  try {
    const data = await analysisApi.getCorrelation()
    if (data) correlationData.value = data
  } catch (e) {
    console.error('Failed to fetch correlation data', e)
  } finally {
    loading.value = false
  }
}

const fetchComparison = async () => {
  loading.value = true
  try {
    const data = await analysisApi.getPeriodComparison(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined,
      period2Start.value ? parseInt(period2Start.value) : undefined,
      period2End.value ? parseInt(period2End.value) : undefined
    )
    if (data) comparisonData.value = data
  } catch (e) {
    console.error('Failed to fetch comparison data', e)
  } finally {
    loading.value = false
  }
}

const fetchHeatmap = async () => {
  loading.value = true
  try {
    const data = await analysisApi.getCategoryHeatmap()
    if (data) heatmapData.value = data
  } catch (e) {
    console.error('Failed to fetch heatmap data', e)
  } finally {
    loading.value = false
  }
}

const heatmapMaxValue = computed(() => {
  const vals = heatmapData.value.values.flat()
  return Math.max(...vals, 1)
})

const getHeatmapColor = (value) => {
  const intensity = value / heatmapMaxValue.value
  const r = Math.round(59 + (37 - 59) * intensity)
  const g = Math.round(130 + (99 - 130) * intensity)
  const b = Math.round(246 + (235 - 246) * intensity)
  return `rgb(${r}, ${g}, ${b})`
}

const formatChange = (val) => {
  if (val === null || val === undefined) return '-'
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val}%`
}

const changeClass = (val) => {
  if (val === null || val === undefined) return 'neutral'
  return val >= 0 ? 'positive' : 'negative'
}

const tabs = [
  { id: 'correlation', i18nKey: 'analysis.correlation' },
  { id: 'comparison', i18nKey: 'analysis.comparison' },
  { id: 'heatmap', i18nKey: 'analysis.heatmap' }
]

onMounted(() => {
  fetchCorrelation()
})
</script>

<template>
  <div class="analysis">
    <PageHeader :title="t('analysis.title')" :description="t('analysis.desc')" :loading="loading" @refresh="activeTab === 'correlation' ? fetchCorrelation() : activeTab === 'comparison' ? fetchComparison() : fetchHeatmap()" />

    <div class="tab-nav">
      <button v-for="tab in tabs" :key="tab.id" class="tab-btn" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id; tab.id === 'correlation' ? fetchCorrelation() : tab.id === 'comparison' ? fetchComparison() : fetchHeatmap()">
        {{ t(tab.i18nKey) }}
      </button>
    </div>

    <LoadingSpinner :loading="loading">
      <div v-if="activeTab === 'correlation'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </span>
              {{ t('analysis.readerTypeBorrow') }}
            </h3>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ t('analysis.degree') }}</th>
                <th>{{ t('analysis.totalBorrow') }}</th>
                <th>{{ t('analysis.checkout') }}</th>
                <th>{{ t('analysis.checkin') }}</th>
                <th>{{ t('analysis.renewal') }}</th>
                <th>{{ t('analysis.onlineRenewal') }}</th>
                <th>{{ t('analysis.avgPerReader') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in correlationData.reader_type_borrow" :key="item.degree" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
                <td><span class="type-tag">{{ item.degree_name }}</span></td>
                <td class="count-cell">{{ formatNumber(item.total) }}</td>
                <td class="count-cell">{{ formatNumber(item.cko) }}</td>
                <td class="count-cell">{{ formatNumber(item.cki) }}</td>
                <td class="count-cell">{{ formatNumber(item.reh) }}</td>
                <td class="count-cell">{{ formatNumber(item.rei) }}</td>
                <td class="count-cell">{{ item.avg_per_reader }}</td>
              </tr>
              <tr v-if="correlationData.reader_type_borrow.length === 0" class="empty-row">
                <td colspan="7">{{ t('common.noData') }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="20" x2="18" y2="10"/>
                  <line x1="12" y1="20" x2="12" y2="4"/>
                  <line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
              </span>
              {{ t('analysis.actionDistribution') }}
            </h3>
          </div>
          <div class="distribution-bars">
            <div v-for="item in correlationData.action_distribution" :key="item.action" class="dist-item">
              <div class="dist-label">{{ item.name }}</div>
              <div class="dist-bar-track">
                <div class="dist-bar-fill" :style="{ width: item.percent + '%' }"></div>
              </div>
              <div class="dist-value">{{ formatNumber(item.count) }} ({{ item.percent }}%)</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'comparison'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
              </span>
              {{ t('analysis.periodSettings') }}
            </h3>
          </div>
          <div class="period-inputs">
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
            <button class="compare-btn" @click="fetchComparison">{{ t('analysis.compare') }}</button>
          </div>
        </div>

        <div v-if="comparisonData.period1 && comparisonData.period1.total !== undefined" class="comparison-grid">
          <div v-for="metric in [
            { key: 'total', label: t('analysis.totalCirculation') },
            { key: 'cko', label: t('analysis.checkout') },
            { key: 'cki', label: t('analysis.checkin') },
            { key: 'reh', label: t('analysis.renewal') },
            { key: 'rei', label: t('analysis.onlineRenewal') },
            { key: 'active_readers', label: t('analysis.activeReaders') }
          ]" :key="metric.key" class="compare-card" :class="changeClass(comparisonData.changes[metric.key])">
            <div class="compare-label">{{ metric.label }}</div>
            <div class="compare-values">
              <div class="compare-period">
                <span class="compare-period-label">{{ t('analysis.period1') }}</span>
                <span class="compare-period-value">{{ formatNumber(comparisonData.period1[metric.key] || 0) }}</span>
              </div>
              <div class="compare-arrow">
                <svg v-if="(comparisonData.changes[metric.key] || 0) >= 0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
                </svg>
              </div>
              <div class="compare-period">
                <span class="compare-period-label">{{ t('analysis.period2') }}</span>
                <span class="compare-period-value">{{ formatNumber(comparisonData.period2[metric.key] || 0) }}</span>
              </div>
            </div>
            <div class="compare-change" :class="changeClass(comparisonData.changes[metric.key])">
              {{ formatChange(comparisonData.changes[metric.key]) }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'heatmap'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="7" height="7" rx="1"/>
                  <rect x="14" y="3" width="7" height="7" rx="1"/>
                  <rect x="3" y="14" width="7" height="7" rx="1"/>
                  <rect x="14" y="14" width="7" height="7" rx="1"/>
                </svg>
              </span>
              {{ t('analysis.categoryHeatmap') }}
            </h3>
          </div>
          <div v-if="heatmapData.categories.length" class="heatmap-container">
            <div class="heatmap-scroll">
              <table class="heatmap-table">
                <thead>
                  <tr>
                    <th class="heatmap-cat-header">{{ t('analysis.category') }}</th>
                    <th v-for="month in heatmapData.months" :key="month" class="heatmap-month-header">{{ month }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(cat, ci) in heatmapData.categories" :key="cat">
                    <td class="heatmap-cat-cell">{{ cat }}</td>
                    <td v-for="(val, mi) in heatmapData.values[ci]" :key="mi" class="heatmap-cell" :style="{ backgroundColor: getHeatmapColor(val) }" :title="`${cat} - ${heatmapData.months[mi]}: ${val}`">
                      <span v-if="val > 0" class="heatmap-val">{{ val }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="heatmap-legend">
              <span class="legend-label">{{ t('analysis.low') }}</span>
              <div class="legend-bar">
                <div v-for="i in 5" :key="i" class="legend-block" :style="{ backgroundColor: getHeatmapColor(i / 5 * heatmapMaxValue) }"></div>
              </div>
              <span class="legend-label">{{ t('analysis.high') }}</span>
            </div>
          </div>
          <div v-else class="empty-state">{{ t('common.noData') }}</div>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.analysis { padding: 0; }

.tab-nav { display: flex; gap: 4px; margin-bottom: 20px; background: var(--color-bg-secondary, #f1f5f9); border-radius: 10px; padding: 4px; }
.tab-btn { flex: 1; padding: 10px 16px; border: none; background: transparent; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; color: var(--color-text-secondary, #64748b); transition: all 0.2s; }
.tab-btn.active { background: var(--color-bg-primary, #fff); color: var(--color-text-primary, #1e293b); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.tab-btn:hover:not(.active) { color: var(--color-text-primary, #1e293b); }

.card { background: var(--color-bg-primary, #fff); border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card-header { display: flex; align-items: center; margin-bottom: 16px; }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: var(--color-text-primary, #1e293b); margin: 0; }
.title-icon { display: flex; align-items: center; width: 20px; height: 20px; color: var(--chart-primary, #3b82f6); }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th { padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: var(--color-text-secondary, #64748b); text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid var(--color-border, #e2e8f0); }
.data-table td { padding: 10px 12px; font-size: 14px; color: var(--color-text-primary, #1e293b); border-bottom: 1px solid var(--color-border, #f1f5f9); }
.table-row { animation: fadeInRow 0.3s ease both; animation-delay: var(--delay); }
@keyframes fadeInRow { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.empty-row td { text-align: center; color: var(--color-text-tertiary, #94a3b8); padding: 24px; }

.type-tag { display: inline-block; padding: 2px 10px; border-radius: 6px; font-size: 13px; font-weight: 500; background: var(--color-bg-secondary, #f1f5f9); color: var(--color-text-primary, #1e293b); }
.count-cell { font-variant-numeric: tabular-nums; font-weight: 500; }

.distribution-bars { display: flex; flex-direction: column; gap: 12px; }
.dist-item { display: grid; grid-template-columns: 80px 1fr 140px; align-items: center; gap: 12px; }
.dist-label { font-size: 13px; font-weight: 500; color: var(--color-text-secondary, #64748b); }
.dist-bar-track { height: 8px; background: var(--color-bg-secondary, #f1f5f9); border-radius: 4px; overflow: hidden; }
.dist-bar-fill { height: 100%; background: var(--chart-primary, #3b82f6); border-radius: 4px; transition: width 0.5s ease; }
.dist-value { font-size: 13px; color: var(--color-text-secondary, #64748b); font-variant-numeric: tabular-nums; }

.period-inputs { display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end; }
.period-group { display: flex; flex-direction: column; gap: 6px; }
.period-group label { font-size: 13px; font-weight: 500; color: var(--color-text-secondary, #64748b); }
.input-row { display: flex; align-items: center; gap: 6px; }
.period-input { padding: 8px 12px; border: 1px solid var(--color-border, #e2e8f0); border-radius: 8px; font-size: 14px; width: 120px; background: var(--color-bg-primary, #fff); color: var(--color-text-primary, #1e293b); }
.period-input:focus { outline: none; border-color: var(--chart-primary, #3b82f6); box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.input-sep { color: var(--color-text-tertiary, #94a3b8); }
.compare-btn { padding: 8px 20px; background: var(--chart-primary, #3b82f6); color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
.compare-btn:hover { background: var(--chart-primary-light, #60a5fa); }

.comparison-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.compare-card { background: var(--color-bg-primary, #fff); border-radius: 10px; padding: 16px; border-left: 3px solid var(--color-border, #e2e8f0); transition: all 0.2s; }
.compare-card.positive { border-left-color: var(--chart-secondary, #10b981); }
.compare-card.negative { border-left-color: var(--chart-danger, #ef4444); }
.compare-label { font-size: 13px; color: var(--color-text-secondary, #64748b); margin-bottom: 10px; font-weight: 500; }
.compare-values { display: flex; align-items: center; gap: 12px; }
.compare-period { display: flex; flex-direction: column; gap: 2px; }
.compare-period-label { font-size: 11px; color: var(--color-text-tertiary, #94a3b8); }
.compare-period-value { font-size: 18px; font-weight: 700; color: var(--color-text-primary, #1e293b); font-variant-numeric: tabular-nums; }
.compare-arrow { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; }
.compare-arrow svg { width: 20px; height: 20px; }
.compare-card.positive .compare-arrow svg { color: var(--chart-secondary, #10b981); }
.compare-card.negative .compare-arrow svg { color: var(--chart-danger, #ef4444); }
.compare-change { margin-top: 8px; font-size: 14px; font-weight: 600; font-variant-numeric: tabular-nums; }
.compare-change.positive { color: var(--chart-secondary, #10b981); }
.compare-change.negative { color: var(--chart-danger, #ef4444); }
.compare-change.neutral { color: var(--color-text-tertiary, #94a3b8); }

.heatmap-container { display: flex; flex-direction: column; gap: 16px; }
.heatmap-scroll { overflow-x: auto; }
.heatmap-table { border-collapse: collapse; min-width: 100%; }
.heatmap-cat-header { padding: 8px 12px; text-align: left; font-size: 12px; font-weight: 600; color: var(--color-text-secondary, #64748b); border-bottom: 2px solid var(--color-border, #e2e8f0); white-space: nowrap; }
.heatmap-month-header { padding: 8px 6px; text-align: center; font-size: 11px; font-weight: 600; color: var(--color-text-secondary, #64748b); border-bottom: 2px solid var(--color-border, #e2e8f0); min-width: 48px; }
.heatmap-cat-cell { padding: 6px 12px; font-size: 12px; color: var(--color-text-primary, #1e293b); white-space: nowrap; border-bottom: 1px solid var(--color-border, #f1f5f9); font-weight: 500; }
.heatmap-cell { padding: 4px; text-align: center; border-bottom: 1px solid var(--color-border, #f1f5f9); border-right: 1px solid var(--color-border, #f1f5f9); min-width: 48px; height: 36px; transition: transform 0.15s; }
.heatmap-cell:hover { transform: scale(1.1); z-index: 1; }
.heatmap-val { font-size: 10px; color: #fff; font-weight: 500; }
.heatmap-legend { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.legend-label { font-size: 11px; color: var(--color-text-tertiary, #94a3b8); }
.legend-bar { display: flex; gap: 2px; }
.legend-block { width: 20px; height: 12px; border-radius: 2px; }
.empty-state { text-align: center; padding: 40px; color: var(--color-text-tertiary, #94a3b8); }
</style>
