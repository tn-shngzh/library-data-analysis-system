<script setup>
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '@/stores/data'
import { LineChart, HeatmapChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent } from 'echarts/components'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'

use([LineChart, HeatmapChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent])

const { t } = useI18n()
const dataStore = useDataStore()

const emit = defineEmits(['navigate'])

const props = defineProps({
  allData: {
    type: Object,
    required: true
  }
})

const s = computed(() => props.allData?.overview?.stats || {})
const h = computed(() => props.allData?.overview?.historicalStats || {})

const formatNum = (val) => {
  if (val === null || val === undefined || val === 0) return '-'
  if (val >= 10000) return (val / 10000).toFixed(1) + 'w'
  if (val >= 1000) return (val / 1000).toFixed(1) + 'k'
  return String(val)
}

const formatPct = (val) => {
  if (val === null || val === undefined) return '-'
  const sign = val >= 0 ? '+' : ''
  return `${sign}${val}%`
}

const todayInsight = computed(() => {
  const stats = s.value
  if (!stats?.total_borrows) return []

  const dod = stats.dod_changes || {}

  return [
    {
      key: 'visits',
      label: t('overview.todayVisits'),
      value: formatNum(stats.today_visits || 0),
      change: dod.visits != null ? dod.visits : null
    },
    {
      key: 'borrows',
      label: t('overview.todayBorrows'),
      value: formatNum(stats.today_borrows || 0),
      change: dod.borrows != null ? dod.borrows : null
    },
    {
      key: 'returns',
      label: t('overview.todayReturns'),
      value: formatNum(stats.today_returns || 0),
      change: dod.returns != null ? dod.returns : null
    }
  ]
})

const alertItems = computed(() => {
  const stats = s.value
  const hist = h.value
  const health = collectionHealth.value
  const alerts = []

  if (!stats?.total_borrows) return alerts

  const todayTotal = (stats.today_borrows || 0) + (stats.today_returns || 0)
  const avgDaily = hist.avg_daily_circulations || 0
  const todayVsAvg = avgDaily > 0 ? Math.round((todayTotal - avgDaily) / avgDaily * 100) : 0
  const yoyBorrows = stats.yoy_changes?.total_borrows ?? null
  const bookTurnover = hist.book_turnover_rate || 0
  const dodVisits = stats.dod_changes?.visits ?? null
  const dodBorrows = stats.dod_changes?.borrows ?? null
  const dodReturns = stats.dod_changes?.returns ?? null
  const neverBorrowed = hist.never_borrowed_books || 0
  const totalBooks = hist.total_distinct_books || 1
  const retentionRate = hist.reader_retention_rate || 0
  const utilization = health.utilization || 0

  if (Math.abs(todayVsAvg) >= 30) {
    const isBelow = todayVsAvg < 0
    alerts.push({
      key: 'today',
      type: 'danger',
      text: t('overview.alertTodayAbnormal') + ' — ' +
        (isBelow ? t('overview.alertBelowAvg', [Math.abs(todayVsAvg)]) : t('overview.alertAboveAvg', [todayVsAvg]))
    })
  } else if (Math.abs(todayVsAvg) >= 15) {
    const isBelow = todayVsAvg < 0
    alerts.push({
      key: 'today',
      type: 'warning',
      text: t('overview.alertTodayAbnormal') + ' — ' +
        (isBelow ? t('overview.alertBelowAvg', [Math.abs(todayVsAvg)]) : t('overview.alertAboveAvg', [todayVsAvg]))
    })
  }

  if (yoyBorrows !== null && yoyBorrows < -10) {
    alerts.push({
      key: 'yoy',
      type: 'danger',
      text: t('overview.alertYoyDecline', [Math.abs(yoyBorrows)])
    })
  } else if (yoyBorrows !== null && yoyBorrows < 0) {
    alerts.push({
      key: 'yoy',
      type: 'warning',
      text: t('overview.alertYoyDecline', [Math.abs(yoyBorrows)])
    })
  }

  if (bookTurnover < 25 && bookTurnover > 0) {
    alerts.push({
      key: 'turnover',
      type: 'danger',
      text: t('overview.alertTurnoverLow', [bookTurnover])
    })
  } else if (bookTurnover < 40 && bookTurnover > 0) {
    alerts.push({
      key: 'turnover',
      type: 'warning',
      text: t('overview.alertTurnoverLow', [bookTurnover])
    })
  }

  if (dodVisits !== null && dodVisits <= -20) {
    alerts.push({
      key: 'dodVisits',
      type: 'danger',
      text: t('overview.alertVisitsDrop', [Math.abs(dodVisits)])
    })
  } else if (dodVisits !== null && dodVisits <= -10) {
    alerts.push({
      key: 'dodVisits',
      type: 'warning',
      text: t('overview.alertVisitsDrop', [Math.abs(dodVisits)])
    })
  }

  if (dodBorrows !== null && dodBorrows <= -15) {
    alerts.push({
      key: 'dodBorrows',
      type: 'danger',
      text: t('overview.alertBorrowsDrop', [Math.abs(dodBorrows)])
    })
  } else if (dodBorrows !== null && dodBorrows <= -5) {
    alerts.push({
      key: 'dodBorrows',
      type: 'warning',
      text: t('overview.alertBorrowsDrop', [Math.abs(dodBorrows)])
    })
  }

  if (dodReturns !== null && dodReturns >= 30) {
    alerts.push({
      key: 'dodReturns',
      type: 'warning',
      text: t('overview.alertReturnsSurge', [dodReturns])
    })
  }

  const neverBorrowPct = Math.round(neverBorrowed / totalBooks * 100)
  if (neverBorrowPct >= 50) {
    alerts.push({
      key: 'neverBorrowed',
      type: 'danger',
      text: t('overview.alertNeverBorrowed', [neverBorrowPct])
    })
  } else if (neverBorrowPct >= 30) {
    alerts.push({
      key: 'neverBorrowed',
      type: 'warning',
      text: t('overview.alertNeverBorrowed', [neverBorrowPct])
    })
  }

  if (retentionRate > 0 && retentionRate < 60) {
    alerts.push({
      key: 'retention',
      type: 'danger',
      text: t('overview.alertRetentionLow', [retentionRate])
    })
  } else if (retentionRate > 0 && retentionRate < 75) {
    alerts.push({
      key: 'retention',
      type: 'warning',
      text: t('overview.alertRetentionLow', [retentionRate])
    })
  }

  if (utilization > 0 && utilization < 60) {
    alerts.push({
      key: 'utilization',
      type: 'danger',
      text: t('overview.alertUtilizationLow', [utilization])
    })
  } else if (utilization > 0 && utilization < 75) {
    alerts.push({
      key: 'utilization',
      type: 'warning',
      text: t('overview.alertUtilizationLow', [utilization])
    })
  }

  return alerts.slice(0, 5)
})

const trend7dOption = computed(() => {
  const data = props.allData?.overview?.trend7d
  if (!data || !Array.isArray(data) || data.length === 0) return null

  const dates = data.map(d => {
    const s = String(d.date)
    return s.length === 8 ? `${s.slice(4, 6)}/${s.slice(6, 8)}` : s
  })
  const borrows = data.map(d => d.borrows || 0)
  const returns = data.map(d => d.returns || 0)
  const total = data.map(d => d.total || 0)
  const borrowers = data.map(d => d.borrowers || 0)

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: 'var(--color-neutral-200)',
      textStyle: { fontSize: 12, color: '#333' }
    },
    legend: {
      data: [t('overview.trendTotal'), t('overview.trendBorrows'), t('overview.trendReturns'), t('overview.trendBorrowers')],
      bottom: 0,
      textStyle: { fontSize: 11, color: '#999' },
      itemWidth: 14,
      itemHeight: 3
    },
    grid: { top: 10, right: 50, bottom: 30, left: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#9ca3af' }
    },
    yAxis: [
      {
        type: 'value',
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
        axisLabel: { fontSize: 10, color: '#9ca3af' }
      },
      {
        type: 'value',
        splitLine: { show: false },
        axisLabel: { fontSize: 10, color: '#ec4899' },
        nameTextStyle: { color: '#ec4899', fontSize: 10 }
      }
    ],
    series: [
      {
        name: t('overview.trendTotal'),
        type: 'line',
        data: total,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2.5, color: '#6366f1' },
        itemStyle: { color: '#6366f1' },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(99,102,241,0.15)' }, { offset: 1, color: 'rgba(99,102,241,0)' }] } }
      },
      {
        name: t('overview.trendBorrows'),
        type: 'line',
        data: borrows,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 1.5, color: '#f59e0b' },
        itemStyle: { color: '#f59e0b' }
      },
      {
        name: t('overview.trendReturns'),
        type: 'line',
        data: returns,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 1.5, color: '#10b981' },
        itemStyle: { color: '#10b981' }
      },
      {
        name: t('overview.trendBorrowers'),
        type: 'line',
        yAxisIndex: 1,
        data: borrowers,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 5,
        lineStyle: { width: 2, color: '#ec4899', type: 'dashed' },
        itemStyle: { color: '#ec4899' }
      }
    ]
  }
})

const collectionHealth = computed(() => {
  return props.allData?.overview?.collectionHealth || { total_books: 0, borrowed_books: 0, zero_borrow: 0, utilization: 0 }
})

const readerHeatmapOption = computed(() => {
  const data = props.allData?.overview?.readerActivityHeatmap
  if (!data || !data.data || data.data.length === 0) return null

  const days = data.days || []
  const hours = data.hours || []
  const maxVal = data.max || 1

  return {
    tooltip: {
      position: 'inside',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e5e7eb',
      textStyle: { fontSize: 11, color: '#333' },
      formatter: (params) => {
        if (!params || params.value === undefined) return ''
        const dayName = days[params.value[1]] || ''
        const hourName = hours[params.value[0]] || ''
        return `${dayName} ${hourName}<br/>${t('overview.heatmapBorrowers')}: <b>${params.value[2]}</b>`
      }
    },
    grid: { top: 4, right: 8, bottom: 24, left: 40 },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 9, color: '#9ca3af', interval: 1 }
    },
    yAxis: {
      type: 'category',
      data: days,
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 9, color: '#9ca3af' }
    },
    visualMap: {
      min: 0,
      max: maxVal,
      show: false,
      inRange: {
        color: ['#f0f5ff', '#dbeafe', '#bfdbfe', '#93c5fd', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af']
      }
    },
    series: [{
      type: 'heatmap',
      data: data.data,
      emphasis: {
        itemStyle: { shadowBlur: 6, shadowColor: 'rgba(59,130,246,0.4)' }
      },
      itemStyle: { borderColor: '#fff', borderWidth: 1, borderRadius: 2 }
    }]
  }
})

onMounted(() => {
  if (!props.allData?.overview?.stats) {
    dataStore.preloadAll?.()
  }
})
</script>

<template>
  <div class="overview">
    <div class="trend-row">
      <div class="trend-main">
        <div class="dash-card">
          <div class="col-card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="col-card-header-icon trend-icon">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <span>{{ t('overview.trend7d') }}</span>
            <div class="col-card-stats">
              <div class="col-stat">
                <span class="col-stat-label">{{ t('overview.totalFlow') }}</span>
                <span class="col-stat-value">{{ formatNum(s.total_borrows || 0) }}</span>
              </div>
              <div class="col-stat">
                <span class="col-stat-label">{{ t('overview.activeReaderRate') }}</span>
                <span class="col-stat-value">{{ s.total_readers > 0 ? Math.round((s.active_readers || 0) / s.total_readers * 1000) / 10 : 0 }}%</span>
              </div>
            </div>
          </div>
          <div class="dash-chart-wrap">
            <v-chart v-if="trend7dOption" class="dash-chart" :option="trend7dOption" autoresize />
            <div v-else class="col-card-empty">
              <span>{{ t('common.noData') }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="trend-side">
        <div class="dash-card">
          <div class="col-card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="col-card-header-icon alert-icon">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <span>{{ t('overview.alerts') }}</span>
            <div class="col-card-stats">
              <div class="col-stat">
                <span class="col-stat-label">{{ t('overview.bookTurnoverRate') }}</span>
                <span class="col-stat-value">{{ h.book_turnover_rate || 0 }}%</span>
              </div>
              <div class="col-stat">
                <span class="col-stat-label">{{ t('overview.opsHealth') }}</span>
                <span class="col-stat-value">{{ (s.today_borrows || 0) + (s.today_returns || 0) }}</span>
              </div>
            </div>
          </div>
          <div class="col-card-body">
            <div v-for="alert in alertItems" :key="alert.key" class="alert-line" :class="alert.type">
              <svg v-if="alert.type === 'danger'" viewBox="0 0 24 24" fill="currentColor" class="alert-line-icon danger-icon">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="16" r="1"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="currentColor" class="alert-line-icon warning-icon">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
                <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="17" r="1"/>
              </svg>
              <span class="alert-line-text">{{ alert.text }}</span>
            </div>
            <div v-if="alertItems.length === 0" class="col-card-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="col-card-empty-icon">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <span>{{ t('overview.noAlerts') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-row">
      <div class="bottom-left">
        <div class="col-card">
          <div class="col-card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="col-card-header-icon heatmap-icon">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
            </svg>
            <span>{{ t('overview.readerActivityHeatmap') }}</span>
          </div>
          <div class="col-card-body">
            <v-chart v-if="readerHeatmapOption" class="heatmap-chart" :option="readerHeatmapOption" autoresize />
            <div v-else class="col-card-empty">
              <span>{{ t('common.noData') }}</span>
            </div>
          </div>
        </div>
      </div>
      <div class="bottom-right">
        <div class="col-card">
          <div class="col-card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="col-card-header-icon bell-icon">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span>{{ t('overview.todayInsights') }}</span>
          </div>
        <div class="col-card-body">
          <div v-for="item in todayInsight" :key="item.key" class="insight-row-item">
            <div class="insight-row-top">
              <div class="insight-row-label-wrap">
                <span class="insight-row-dot" :class="item.key"></span>
                <span class="insight-row-label">{{ item.label }}</span>
              </div>
              <span v-if="item.change != null" class="insight-row-change" :class="item.change >= 0 ? 'up' : 'down'">
                {{ formatPct(item.change) }}
              </span>
            </div>
            <span class="insight-row-value">{{ item.value }}</span>
          </div>
          <div class="health-divider"></div>
          <div class="health-body-row">
            <div class="health-ring-wrap-sm">
              <svg viewBox="0 0 36 36" class="health-ring">
                <path class="health-ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="health-ring-fill" :stroke-dasharray="`${collectionHealth.utilization}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div class="health-ring-label">
                <span class="health-ring-pct">{{ collectionHealth.utilization }}%</span>
                <span class="health-ring-sub">{{ t('overview.healthUtil') }}</span>
              </div>
            </div>
            <div class="health-stats-compact">
              <div class="health-stat">
                <span class="health-stat-label">{{ t('overview.healthTotalBooks') }}</span>
                <span class="health-stat-value">{{ formatNum(collectionHealth.total_books) }}</span>
              </div>
              <div class="health-stat">
                <span class="health-stat-label">{{ t('overview.healthBorrowedBooks') }}</span>
                <span class="health-stat-value">{{ formatNum(collectionHealth.borrowed_books) }}</span>
              </div>
              <div class="health-stat">
                <span class="health-stat-label">{{ t('overview.healthZeroBorrow') }}</span>
                <span class="health-stat-value warn">{{ formatNum(collectionHealth.zero_borrow) }}</span>
              </div>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  height: calc(100vh - 120px);
  overflow: hidden;
}

.trend-row {
  display: flex;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.trend-main {
  flex: 7;
  min-width: 0;
}

.trend-side {
  flex: 3;
  min-width: 0;
}

.bottom-row {
  display: flex;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.bottom-left {
  flex: 7;
  min-width: 0;
}

.bottom-right {
  flex: 3;
  min-width: 0;
}

.bottom-left .col-card,
.bottom-right .col-card {
  height: 100%;
}

.col-card {
  flex: 1;
  background: var(--chart-bg);
  backdrop-filter: blur(12px) saturate(1.1);
  -webkit-backdrop-filter: blur(12px) saturate(1.1);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.col-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--color-neutral-800);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-neutral-100);
  flex-shrink: 0;
}

.col-card-stats {
  display: flex;
  gap: var(--space-4);
  flex: 1;
  justify-content: flex-end;
  min-width: 0;
}

.col-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
}

.col-stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  white-space: nowrap;
}

.col-stat-value {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  white-space: nowrap;
}

.col-card-header-icon {
  width: 15px;
  height: 15px;
}

.col-card-header-icon.bell-icon {
  color: var(--data-borrow);
}

.col-card-header-icon.alert-icon {
  color: var(--color-danger-500);
}

.col-card-header-icon.stats-icon {
  color: var(--data-book);
}

.col-card-header-icon.trend-icon {
  color: #6366f1;
}

.col-card-header-icon.health-icon {
  color: var(--color-success-500);
}

.col-card-header-icon.anomaly-icon {
  color: var(--color-warning-500);
}

.col-card-header-icon.heatmap-icon {
  color: #3b82f6;
}

.col-card-body {
  padding: var(--space-2) 0 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

.col-card-empty {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
  flex: 1;
  justify-content: center;
}

.col-card-empty-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.insight-row-item {
  padding: var(--space-2) var(--space-1);
  border-radius: var(--radius-md);
  transition: background 0.15s ease;
  flex-shrink: 0;
}

.insight-row-item:hover {
  background: rgba(0,0,0,0.02);
}

.insight-row-item + .insight-row-item {
  border-top: 1px solid var(--color-neutral-100);
}

.insight-row-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-1);
}

.insight-row-label-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.insight-row-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.insight-row-dot.visits {
  background: var(--data-visit);
  box-shadow: 0 0 6px rgba(80,227,194,0.4);
}

.insight-row-dot.borrows {
  background: var(--data-borrow);
  box-shadow: 0 0 6px rgba(245,166,35,0.4);
}

.insight-row-dot.returns {
  background: var(--data-return);
  box-shadow: 0 0 6px rgba(126,211,33,0.4);
}

.insight-row-label {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.insight-row-change {
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  padding: 1px 6px;
  border-radius: var(--radius-full);
}

.insight-row-change.up {
  color: var(--color-success-600);
  background: rgba(16,185,129,0.1);
}

.insight-row-change.down {
  color: var(--color-danger-600);
  background: rgba(239,68,68,0.1);
}

.insight-row-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  letter-spacing: var(--tracking-tight);
  padding-left: calc(8px + var(--space-2));
}

.health-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-neutral-200), transparent);
  margin: var(--space-1) 0;
  flex-shrink: 0;
}

.alert-line {
  padding: var(--space-2) var(--space-1);
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  border-radius: var(--radius-md);
  transition: background 0.15s ease;
}

.alert-line:hover {
  background: rgba(0,0,0,0.02);
}

.alert-line + .alert-line {
  border-top: none;
  margin-top: var(--space-1);
}

.alert-line-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.alert-line-icon.danger-icon {
  color: var(--color-danger-500);
  filter: drop-shadow(0 0 4px rgba(239,68,68,0.35));
}

.alert-line-icon.warning-icon {
  color: var(--color-warning-500, #f59e0b);
  filter: drop-shadow(0 0 4px rgba(245,158,11,0.35));
}

.alert-line.danger {
  background: rgba(239,68,68,0.04);
  border-left: 3px solid var(--color-danger-500);
  padding-left: var(--space-2);
}

.alert-line.danger .alert-line-text {
  color: var(--color-danger-700);
  font-weight: var(--font-medium);
}

.alert-line.warning {
  background: rgba(245,158,11,0.04);
  border-left: 3px solid var(--color-warning-500, #f59e0b);
  padding-left: var(--space-2);
}

.alert-line.warning .alert-line-text {
  color: var(--color-warning-700, #b45309);
  font-weight: var(--font-medium);
}

.alert-line-text {
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
  line-height: 1.5;
}

.dash-card {
  background: var(--chart-bg);
  backdrop-filter: blur(12px) saturate(1.1);
  -webkit-backdrop-filter: blur(12px) saturate(1.1);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.dash-chart-wrap {
  flex: 1;
  min-height: 0;
}

.dash-chart {
  width: 100%;
  height: 100%;
  min-height: 180px;
}

.heatmap-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.health-body {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) 0;
  min-height: 0;
}

.health-body-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
}

.health-ring-wrap {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
}

.health-ring-wrap-sm {
  position: relative;
  width: 56px;
  height: 56px;
  flex-shrink: 0;
}

.health-ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.health-ring-bg {
  fill: none;
  stroke: var(--color-neutral-100);
  stroke-width: 3;
}

.health-ring-fill {
  fill: none;
  stroke: var(--color-success-500);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.8s ease;
}

.health-ring-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.health-ring-pct {
  font-size: var(--text-base);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  line-height: 1;
}

.health-ring-sub {
  font-size: 9px;
  color: var(--color-neutral-400);
  margin-top: 1px;
}

.health-ring-text {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  margin-top: 2px;
}

.health-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.health-stats-compact {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.health-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
}

.health-stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
}

.health-stat-value {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--color-neutral-800);
}

.health-stat-value.warn {
  color: var(--color-danger-500);
}

@media (max-width: 1200px) {
  .trend-row {
    flex-direction: column;
  }
  .trend-main, .trend-side {
    flex: none;
  }
  .bottom-row {
    flex-direction: column;
  }
  .bottom-left, .bottom-right {
    flex: none;
  }
}

@media (max-width: 768px) {
  .col-card-stats {
    flex-direction: column;
    gap: var(--space-1);
  }
}


</style>
