<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatNumber } from '@/utils/format'
import { insightsApi } from '@/api/insights'
import { useDataStore } from '@/stores/data'
import InsightsPanel from '@/components/InsightsPanel.vue'

const { t } = useI18n()
const dataStore = useDataStore()

const emit = defineEmits(['navigate'])

const props = defineProps({
  allData: {
    type: Object,
    required: true
  }
})

const insights = ref([])
const loadError = ref(false)

watch(() => dataStore.loaded, (loaded) => {
  if (loaded && !props.allData?.overview?.stats) {
    loadError.value = true
  }
})

const retryLoad = async () => {
  loadError.value = false
  await dataStore.refreshModule('overview')
  if (!props.allData?.overview?.stats) {
    loadError.value = true
  }
}

const cardNavMap = {
  total_flow: 'borrow',
  registered_readers: 'reader',
  active_readers: 'reader',
  books_in_library: 'book',
  borrowed_books: 'borrow',
  returned_books: 'borrow',
  library_visits: 'borrow',
  online_renewals: 'borrow',
  total_categories: 'category',
  today_borrows: 'borrow',
  today_returns: 'borrow',
  today_visits: 'borrow',
  borrow_rate: 'borrow',
  active_rate: 'reader',
  avg_borrow: 'borrow',
  never_borrowed: 'book'
}

const handleCardClick = (card) => {
  const targetTab = cardNavMap[card.key]
  if (targetTab) emit('navigate', targetTab)
}

const statsCards = computed(() => {
  const s = props.allData?.overview?.stats
  const h = props.allData?.overview?.historicalStats
  if (!s) {
    return [
      { key: 'total_flow', label: t('overview.totalFlow'), value: '-', change: '-', changeType: 'up', icon: 'book', color: 'var(--chart-primary)' },
      { key: 'registered_readers', label: t('overview.registeredReaders'), value: '-', change: '-', changeType: 'up', icon: 'users', color: 'var(--color-info-500)' },
      { key: 'active_readers', label: t('overview.activeReaders'), value: '-', change: '-', changeType: 'up', icon: 'user-check', color: 'var(--chart-accent)' },
      { key: 'books_in_library', label: t('overview.booksInLibrary'), value: '-', change: '-', changeType: 'up', icon: 'archive', color: 'var(--chart-secondary-light)' },
      { key: 'borrowed_books', label: t('overview.borrowedBooks'), value: '-', change: '-', changeType: 'up', icon: 'arrow-up', color: 'var(--chart-primary-light)' },
      { key: 'returned_books', label: t('overview.returnedBooks'), value: '-', change: '-', changeType: 'up', icon: 'arrow-down', color: 'var(--chart-danger)' },
      { key: 'library_visits', label: t('overview.libraryRenewals'), value: '-', change: '-', changeType: 'up', icon: 'refresh', color: 'var(--chart-secondary)' },
      { key: 'online_renewals', label: t('overview.onlineRenewals'), value: '-', change: '-', changeType: 'up', icon: 'wifi', color: 'var(--chart-primary)' },
      { key: 'total_categories', label: t('overview.totalCategories'), value: '-', change: '-', changeType: 'neutral', icon: 'layers', color: 'var(--chart-accent)' },
      { key: 'today_borrows', label: t('overview.todayBorrows'), value: '-', change: '-', changeType: 'up', icon: 'book-open', color: 'var(--chart-primary-light)' },
      { key: 'today_returns', label: t('overview.todayReturns'), value: '-', change: '-', changeType: 'up', icon: 'book-closed', color: 'var(--chart-danger)' },
      { key: 'today_visits', label: t('overview.todayVisits'), value: '-', change: '-', changeType: 'up', icon: 'map-pin', color: 'var(--chart-accent)' },
      { key: 'borrow_rate', label: t('overview.borrowRate'), value: '-', rate: 0, icon: 'percent', color: 'var(--chart-primary)' },
      { key: 'active_rate', label: t('overview.activeReaderRate'), value: '-', rate: 0, icon: 'activity', color: 'var(--color-info-500)' },
      { key: 'avg_borrow', label: t('overview.avgBorrowPerReader'), value: '-', unit: t('overview.times'), icon: 'trending-up', color: 'var(--chart-secondary-light)' },
      { key: 'never_borrowed', label: t('overview.neverBorrowedBooks'), value: '-', icon: 'book-off', color: 'var(--chart-danger)' }
    ]
  }
  const yoy = s?.yoy_changes || {}
  const dod = s?.dod_changes || {}
  const fmtChange = (key) => {
    const val = yoy[key]
    if (val === null || val === undefined) return t('common.noData')
    const sign = val >= 0 ? '+' : ''
    return `${sign}${val}%`
  }
  const fmtChangeType = (key) => {
    const val = yoy[key]
    if (val === null || val === undefined) return 'neutral'
    return val >= 0 ? 'up' : 'down'
  }
  const fmtDod = (key) => {
    const val = dod[key]
    if (val === null || val === undefined) return t('common.noData')
    const sign = val >= 0 ? '+' : ''
    return `${sign}${val}%`
  }
  const fmtDodType = (key) => {
    const val = dod[key]
    if (val === null || val === undefined) return 'neutral'
    return val >= 0 ? 'up' : 'down'
  }
  const borrowRate = s.total_books > 0 ? Math.round((s.cko_count || 0) / s.total_books * 1000) / 10 : 0
  const activeRate = s.total_readers > 0 ? Math.round((s.active_readers || 0) / s.total_readers * 1000) / 10 : 0
  const avgBorrow = s.total_readers > 0 ? Math.round((s.total_borrows || 0) / s.total_readers * 10) / 10 : 0
  const neverBorrowed = h?.never_borrowed_books || 0
  return [
    { key: 'total_flow', label: t('overview.totalFlow'), value: formatNumber(s.total_borrows || 0), change: fmtChange('total_borrows'), changeType: fmtChangeType('total_borrows'), icon: 'book', color: 'var(--chart-primary)' },
    { key: 'registered_readers', label: t('overview.registeredReaders'), value: formatNumber(s.total_readers || 0), change: fmtChange('total_readers'), changeType: fmtChangeType('total_readers'), icon: 'users', color: 'var(--color-info-500)' },
    { key: 'active_readers', label: t('overview.activeReaders'), value: formatNumber(s.active_readers || 0), change: fmtChange('active_readers'), changeType: fmtChangeType('active_readers'), icon: 'user-check', color: 'var(--chart-accent)' },
    { key: 'books_in_library', label: t('overview.booksInLibrary'), value: formatNumber(s.total_books || 0), change: fmtChange('total_books'), changeType: fmtChangeType('total_books'), icon: 'archive', color: 'var(--chart-secondary-light)' },
    { key: 'borrowed_books', label: t('overview.borrowedBooks'), value: formatNumber(s.cko_count || 0), change: fmtChange('cko_count'), changeType: fmtChangeType('cko_count'), icon: 'arrow-up', color: 'var(--chart-primary-light)' },
    { key: 'returned_books', label: t('overview.returnedBooks'), value: formatNumber(s.cki_count || 0), change: fmtChange('cki_count'), changeType: fmtChangeType('cki_count'), icon: 'arrow-down', color: 'var(--chart-danger)' },
    { key: 'library_visits', label: t('overview.libraryRenewals'), value: formatNumber(s.reh_count || 0), change: fmtChange('reh_count'), changeType: fmtChangeType('reh_count'), icon: 'refresh', color: 'var(--chart-secondary)' },
    { key: 'online_renewals', label: t('overview.onlineRenewals'), value: formatNumber(s.rei_count || 0), change: fmtChange('rei_count'), changeType: fmtChangeType('rei_count'), icon: 'wifi', color: 'var(--chart-primary)' },
    { key: 'total_categories', label: t('overview.totalCategories'), value: formatNumber(s.total_categories || 0), change: '-', changeType: 'neutral', icon: 'layers', color: 'var(--chart-accent)' },
    { key: 'today_borrows', label: t('overview.todayBorrows'), value: formatNumber(s.today_borrows || 0), change: fmtDod('borrows'), changeType: fmtDodType('borrows'), changeLabel: 'comparedToYesterday', icon: 'book-open', color: 'var(--chart-primary-light)' },
    { key: 'today_returns', label: t('overview.todayReturns'), value: formatNumber(s.today_returns || 0), change: fmtDod('returns'), changeType: fmtDodType('returns'), changeLabel: 'comparedToYesterday', icon: 'book-closed', color: 'var(--chart-danger)' },
    { key: 'today_visits', label: t('overview.todayVisits'), value: formatNumber(s.today_visits || 0), change: fmtDod('visits'), changeType: fmtDodType('visits'), changeLabel: 'comparedToYesterday', icon: 'map-pin', color: 'var(--chart-accent)' },
    { key: 'borrow_rate', label: t('overview.borrowRate'), value: borrowRate + '%', rate: borrowRate, change: '-', changeType: 'neutral', icon: 'percent', color: 'var(--chart-primary)' },
    { key: 'active_rate', label: t('overview.activeReaderRate'), value: activeRate + '%', rate: activeRate, change: '-', changeType: 'neutral', icon: 'activity', color: 'var(--color-info-500)' },
    { key: 'avg_borrow', label: t('overview.avgBorrowPerReader'), value: avgBorrow, unit: t('overview.times'), change: '-', changeType: 'neutral', icon: 'trending-up', color: 'var(--chart-secondary-light)' },
    { key: 'never_borrowed', label: t('overview.neverBorrowedBooks'), value: formatNumber(neverBorrowed), change: '-', changeType: 'neutral', icon: 'book-off', color: 'var(--chart-danger)' }
  ]
})

const rateCards = computed(() => {
  const s = props.allData?.overview?.stats
  if (!s) return []
  const borrowRate = s.total_books > 0 ? Math.round((s.cko_count || 0) / s.total_books * 1000) / 10 : 0
  const activeRate = s.total_readers > 0 ? Math.round((s.active_readers || 0) / s.total_readers * 1000) / 10 : 0
  return [
    { key: 'borrow_rate', label: t('overview.borrowRate'), value: borrowRate + '%', rate: borrowRate, color: 'var(--chart-primary)', icon: 'percent' },
    { key: 'active_rate', label: t('overview.activeReaderRate'), value: activeRate + '%', rate: activeRate, color: 'var(--color-info-500)', icon: 'activity' }
  ]
})

const metricCards = computed(() => {
  const s = props.allData?.overview?.stats
  if (!s) return []
  const avgBorrow = s.total_readers > 0 ? Math.round((s.total_borrows || 0) / s.total_readers * 10) / 10 : 0
  const ckoCount = s.cko_count || 0
  const ckiCount = s.cki_count || 0
  const borrowReturnRatio = ckiCount > 0 ? (ckoCount / ckiCount).toFixed(2) : '-'
  return [
    { key: 'avg_borrow', label: t('overview.avgBorrowPerReader'), value: avgBorrow, unit: t('overview.times'), color: 'var(--chart-secondary-light)', icon: 'trending-up' },
    { key: 'borrow_return_ratio', label: t('overview.borrowReturnRatio'), value: borrowReturnRatio, primary: formatNumber(ckoCount), primaryLabel: t('overview.borrowedBooks'), secondary: formatNumber(ckiCount), secondaryLabel: t('overview.returnedBooks'), color: 'var(--chart-danger)', icon: 'scale' }
  ]
})

const historicalCards = computed(() => {
  const h = props.allData?.overview?.historicalStats
  if (!h || h.data_years === 0) return []
  const monthNames = ['', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
  return [
    { key: 'data_years', label: t('overview.dataYears'), value: h.data_years, unit: t('overview.years'), sub: `${h.data_start_year} - ${h.data_end_year}`, color: 'var(--chart-primary)', icon: 'calendar' },
    { key: 'avg_monthly', label: t('overview.avgMonthlyCirc'), value: formatNumber(h.avg_monthly_circulations), unit: t('overview.times'), color: 'var(--chart-secondary)', icon: 'bar-chart' },
    { key: 'avg_daily', label: t('overview.avgDailyCirc'), value: formatNumber(h.avg_daily_circulations), unit: t('overview.times'), color: 'var(--chart-accent)', icon: 'clock' },
    { key: 'peak_month', label: t('overview.peakMonth'), value: monthNames[h.peak_month] || '-', unit: t('overview.month'), sub: `${t('overview.circCount')} ${formatNumber(h.peak_month_count)}`, color: 'var(--chart-danger)', icon: 'peak' },
    { key: 'peak_ym', label: t('overview.peakYearMonth'), value: h.peak_year_month, sub: `${formatNumber(h.peak_ym_count)} ${t('overview.times')}`, color: 'var(--chart-primary-light)', icon: 'trophy' },
    { key: 'book_turnover', label: t('overview.bookTurnoverRate'), value: h.book_turnover_rate + '%', rate: h.book_turnover_rate, color: 'var(--color-info-500)', icon: 'repeat' },
    { key: 'reader_retention', label: t('overview.readerRetentionRate'), value: h.reader_retention_rate + '%', rate: h.reader_retention_rate, color: 'var(--chart-secondary-light)', icon: 'heart' },
    { key: 'renew_rate', label: t('overview.renewRate'), value: h.renew_rate + '%', rate: h.renew_rate, color: 'var(--chart-primary)', icon: 'refresh-rate' },
    { key: 'never_borrowed', label: t('overview.neverBorrowedBooks'), value: formatNumber(h.never_borrowed_books), primary: formatNumber(h.borrowed_distinct_books), primaryLabel: t('overview.everBorrowed'), secondary: formatNumber(h.never_borrowed_books), secondaryLabel: t('overview.neverBorrowed'), color: 'var(--chart-danger)', icon: 'book-off' }
  ]
})

const yearlyTrend = computed(() => {
  const h = props.allData?.overview?.historicalStats
  if (!h || !h.yearly_trend || h.yearly_trend.length === 0) return []
  const reversed = [...h.yearly_trend].reverse()
  const maxCount = Math.max(...reversed.map(item => item.count))
  return reversed.map(item => ({ ...item, maxCount }))
})

onMounted(() => {
  loadInsights()
})

async function loadInsights() {
  try {
    const data = await insightsApi.auto(5)
    if (data) insights.value = data
  } catch (e) { console.error(e) }
}
</script>

<template>
  <div class="overview-container">
    <div v-if="loadError" class="load-error-banner">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <span>{{ t('common.loadFailed') }}</span>
      <button class="retry-btn" @click="retryLoad">{{ t('common.retry') }}</button>
    </div>
    <div class="stats-cards-grid">
      <div
        v-for="(card, index) in statsCards"
        :key="card.key"
        class="stat-card"
        :class="{ 'stat-card-empty': card.value === '-', 'stat-card-clickable': cardNavMap[card.key] }"
        :style="{ '--card-color': card.color, '--delay': (index * 0.04) + 's' }"
        @click="handleCardClick(card)"
      >
        <div class="stat-icon-wrapper">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter" class="stat-icon">
            <template v-if="card.icon === 'book'">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </template>
            <template v-else-if="card.icon === 'users'">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </template>
            <template v-else-if="card.icon === 'user-check'">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="8.5" cy="7" r="4"/>
              <polyline points="17 11 19 13 23 9"/>
            </template>
            <template v-else-if="card.icon === 'archive'">
              <polyline points="21 8 21 21 3 21 3 8"/>
              <rect x="1" y="3" width="22" height="5"/>
              <line x1="10" y1="12" x2="14" y2="12"/>
            </template>
            <template v-else-if="card.icon === 'arrow-up'">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </template>
            <template v-else-if="card.icon === 'arrow-down'">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <polyline points="19 12 12 19 5 12"/>
            </template>
            <template v-else-if="card.icon === 'refresh'">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </template>
            <template v-else-if="card.icon === 'wifi'">
              <path d="M5 12.55a11 11 0 0 1 14.08 0"/>
              <path d="M1.42 9a16 16 0 0 1 21.16 0"/>
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
              <line x1="12" y1="20" x2="12.01" y2="20"/>
            </template>
            <template v-else-if="card.icon === 'layers'">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </template>
            <template v-else-if="card.icon === 'book-open'">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </template>
            <template v-else-if="card.icon === 'book-closed'">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </template>
            <template v-else-if="card.icon === 'map-pin'">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </template>
            <template v-else-if="card.icon === 'percent'">
              <line x1="19" y1="5" x2="5" y2="19"/>
              <circle cx="6.5" cy="6.5" r="2.5"/>
              <circle cx="17.5" cy="17.5" r="2.5"/>
            </template>
            <template v-else-if="card.icon === 'activity'">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </template>
            <template v-else-if="card.icon === 'trending-up'">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </template>
            <template v-else-if="card.icon === 'book-off'">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              <line x1="2" y1="2" x2="22" y2="22"/>
            </template>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">{{ card.label }}</span>
          <div class="stat-value-row">
            <span class="stat-value">{{ card.value }}</span>
            <span v-if="card.unit" class="stat-unit">{{ card.unit }}</span>
          </div>
          <div v-if="card.rate !== undefined" class="stat-progress-track">
            <div class="stat-progress-fill" :style="{ width: Math.min(card.rate, 100) + '%' }"></div>
          </div>
          <div class="stat-change" :class="card.changeType">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-if="card.changeType === 'up'" class="change-icon">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
            <span>{{ t(card.changeLabel ? 'common.' + card.changeLabel : 'common.comparedToLastYear') }} {{ card.change }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="rateCards.length || metricCards.length" class="metrics-section">
      <div v-if="rateCards.length" class="rate-cards-row">
        <div
          v-for="(card, index) in rateCards"
          :key="card.key"
          class="rate-card"
          :style="{ '--card-color': card.color, '--delay': (index * 0.06) + 's' }"
        >
          <div class="rate-card-header">
            <div class="rate-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="rate-icon">
                <template v-if="card.icon === 'percent'">
                  <line x1="19" y1="5" x2="5" y2="19"/>
                  <circle cx="6.5" cy="6.5" r="2.5"/>
                  <circle cx="17.5" cy="17.5" r="2.5"/>
                </template>
                <template v-else-if="card.icon === 'activity'">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </template>
              </svg>
            </div>
            <span class="rate-label">{{ card.label }}</span>
          </div>
          <div class="rate-value-row">
            <span class="rate-value">{{ card.value }}</span>
          </div>
          <div class="rate-progress-track">
            <div class="rate-progress-fill" :style="{ width: Math.min(card.rate, 100) + '%' }"></div>
          </div>
        </div>
      </div>

      <div v-if="metricCards.length" class="metric-cards-row">
        <div
          v-for="(card, index) in metricCards"
          :key="card.key"
          class="metric-card"
          :style="{ '--card-color': card.color, '--delay': (index * 0.06) + 's' }"
        >
          <div class="metric-card-header">
            <div class="metric-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="metric-icon">
                <template v-if="card.icon === 'trending-up'">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </template>
                <template v-else-if="card.icon === 'scale'">
                  <line x1="12" y1="3" x2="12" y2="21"/>
                  <line x1="4" y1="8" x2="20" y2="8"/>
                  <circle cx="4" cy="14" r="2"/>
                  <circle cx="20" cy="14" r="2"/>
                </template>
              </svg>
            </div>
            <span class="metric-label">{{ card.label }}</span>
          </div>
          <div class="metric-value-row">
            <span class="metric-value">{{ card.value }}</span>
            <span v-if="card.unit" class="metric-unit">{{ card.unit }}</span>
          </div>
          <div v-if="card.primary" class="metric-pair">
            <div class="metric-pair-item">
              <span class="pair-label">{{ card.primaryLabel }}</span>
              <span class="pair-value">{{ card.primary }}</span>
            </div>
            <div class="metric-pair-divider"></div>
            <div class="metric-pair-item">
              <span class="pair-label">{{ card.secondaryLabel }}</span>
              <span class="pair-value">{{ card.secondary }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="historicalCards.length" class="historical-section">
      <div class="section-title">{{ t('overview.historicalAnalysis') }}</div>
      <div class="historical-cards-grid">
        <div
          v-for="(card, index) in historicalCards"
          :key="card.key"
          class="hist-card"
          :class="{ 'hist-card-rate': card.rate !== undefined, 'hist-card-compare': card.primary }"
          :style="{ '--card-color': card.color, '--delay': (index * 0.04) + 's' }"
        >
          <div class="hist-card-header">
            <div class="hist-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="hist-icon">
                <template v-if="card.icon === 'calendar'">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </template>
                <template v-else-if="card.icon === 'bar-chart'">
                  <line x1="12" y1="20" x2="12" y2="10"/>
                  <line x1="18" y1="20" x2="18" y2="4"/>
                  <line x1="6" y1="20" x2="6" y2="16"/>
                </template>
                <template v-else-if="card.icon === 'clock'">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </template>
                <template v-else-if="card.icon === 'peak'">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </template>
                <template v-else-if="card.icon === 'trophy'">
                  <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
                  <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
                  <path d="M4 22h16"/>
                  <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>
                  <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>
                  <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
                </template>
                <template v-else-if="card.icon === 'repeat'">
                  <polyline points="17 1 21 5 17 9"/>
                  <path d="M3 11V9a4 4 0 0 1 4-4h14"/>
                  <polyline points="7 23 3 19 7 15"/>
                  <path d="M21 13v2a4 4 0 0 1-4 4H3"/>
                </template>
                <template v-else-if="card.icon === 'heart'">
                  <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                </template>
                <template v-else-if="card.icon === 'refresh-rate'">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </template>
                <template v-else-if="card.icon === 'book-off'">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  <line x1="2" y1="2" x2="22" y2="22"/>
                </template>
              </svg>
            </div>
            <span class="hist-label">{{ card.label }}</span>
          </div>
          <div class="hist-value-row">
            <span class="hist-value">{{ card.value }}</span>
            <span v-if="card.unit" class="hist-unit">{{ card.unit }}</span>
          </div>
          <div v-if="card.sub" class="hist-sub">{{ card.sub }}</div>
          <div v-if="card.rate !== undefined" class="hist-progress-track">
            <div class="hist-progress-fill" :style="{ width: Math.min(card.rate, 100) + '%' }"></div>
          </div>
          <div v-if="card.primary" class="metric-pair">
            <div class="metric-pair-item">
              <span class="pair-label">{{ card.primaryLabel }}</span>
              <span class="pair-value">{{ card.primary }}</span>
            </div>
            <div class="metric-pair-divider"></div>
            <div class="metric-pair-item">
              <span class="pair-label">{{ card.secondaryLabel }}</span>
              <span class="pair-value">{{ card.secondary }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="yearlyTrend.length" class="yearly-trend-card">
        <div class="yearly-trend-title">{{ t('overview.yearlyTrend') }}</div>
        <div class="yearly-bars">
          <div v-for="(item, idx) in yearlyTrend" :key="item.year" class="yearly-bar-item">
            <div class="yearly-bar-track">
              <div
                class="yearly-bar-fill"
                :style="{
                  height: (item.count / item.maxCount * 100) + '%',
                  '--bar-color': idx === yearlyTrend.length - 1 ? 'var(--chart-primary)' : 'var(--chart-secondary-light)'
                }"
              ></div>
            </div>
            <span class="yearly-bar-label">{{ item.year }}</span>
            <span class="yearly-bar-value">{{ formatNumber(item.count) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="insights.length" class="insights-section">
      <InsightsPanel :insights="insights" />
    </div>
  </div>
</template>

<style scoped src="./OverviewView.css"></style>
