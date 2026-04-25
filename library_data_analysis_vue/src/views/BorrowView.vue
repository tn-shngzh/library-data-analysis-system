<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { borrowApi } from '@/api/borrows'
import { formatNumber } from '@/utils/format'
import { BORROW_STAT_CARDS, ACTION_MAP, DEGREE_MAP } from '@/constants'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'

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

const statCards = BORROW_STAT_CARDS
const actionMap = ACTION_MAP
const degreeMap = DEGREE_MAP

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
</script>

<template>
  <div class="borrows">
    <PageHeader :title="t('borrow.title')" :description="t('borrow.desc')" :loading="loading" @refresh="fetchBorrowData" />

    <LoadingSpinner :loading="loading">
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.key" class="stat-card" :style="{ '--accent': card.accent }">
          <div class="stat-info">
            <span class="stat-label">{{ t(card.i18nKey) }}</span>
            <span class="stat-value">{{ formatNumber(borrowStats[card.key]) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </span>
            {{ t('borrow.actionStats') }}
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('borrow.action') }}</th>
              <th>{{ t('borrow.count') }}</th>
              <th>{{ t('borrow.percent') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in actionStats" :key="item.action" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td><span class="type-tag">{{ item.name }}</span></td>
              <td class="count-cell">{{ formatNumber(item.count) }} <span class="unit">{{ t('common.times') }}</span></td>
              <td>
                <div class="percent-bar">
                  <div class="percent-fill" :style="{ width: item.percent + '%' }"></div>
                  <span class="percent-text">{{ item.percent }}%</span>
                </div>
              </td>
            </tr>
            <tr v-if="actionStats.length === 0" class="empty-row">
              <td colspan="3">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

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
            {{ t('borrow.degreeStats') }}
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('borrow.degree') }}</th>
              <th>{{ t('borrow.count') }}</th>
              <th>{{ t('borrow.percent') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in degreeStats" :key="item.code" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td><span class="type-tag">{{ item.name }}</span></td>
              <td class="count-cell">{{ formatNumber(item.count) }} <span class="unit">{{ t('common.times') }}</span></td>
              <td>
                <div class="percent-bar">
                  <div class="percent-fill" :style="{ width: item.percent + '%' }"></div>
                  <span class="percent-text">{{ item.percent }}%</span>
                </div>
              </td>
            </tr>
            <tr v-if="degreeStats.length === 0" class="empty-row">
              <td colspan="3">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="8" r="7"/>
                <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>
              </svg>
            </span>
            {{ t('borrow.topBorrowers') }}
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('borrow.rank') }}</th>
              <th>{{ t('borrow.readerId') }}</th>
              <th>{{ t('borrow.type') }}</th>
              <th>{{ t('borrow.count') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in topBorrowers" :key="item.borrower_id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td>
                <span class="rank-badge" :class="'rank-' + item.rank">{{ item.rank }}</span>
              </td>
              <td class="id-cell">{{ item.borrower_id }}</td>
              <td><span class="type-tag">{{ item.degree }}</span></td>
              <td class="count-cell">{{ formatNumber(item.borrow_count) }} <span class="unit">{{ t('common.times') }}</span></td>
            </tr>
            <tr v-if="topBorrowers.length === 0" class="empty-row">
              <td colspan="4">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </span>
            {{ t('borrow.topBooks') }}
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('borrow.rank') }}</th>
              <th>{{ t('borrow.bookId') }}</th>
              <th>{{ t('borrow.category') }}</th>
              <th>{{ t('borrow.count') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in topBooks" :key="item.bib_id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td>
                <span class="rank-badge" :class="'rank-' + item.rank">{{ item.rank }}</span>
              </td>
              <td class="id-cell">{{ item.bib_id }}</td>
              <td><span class="category-tag">{{ item.category }}</span></td>
              <td class="count-cell">{{ formatNumber(item.borrow_count) }} <span class="unit">{{ t('common.times') }}</span></td>
            </tr>
            <tr v-if="topBooks.length === 0" class="empty-row">
              <td colspan="4">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </span>
            {{ t('borrow.recentBorrows') }}
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('borrow.date') }}</th>
              <th>{{ t('borrow.time') }}</th>
              <th>{{ t('borrow.readerId') }}</th>
              <th>{{ t('borrow.bookId') }}</th>
              <th>{{ t('borrow.type') }}</th>
              <th>{{ t('borrow.category') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in recentBorrows" :key="index" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td>{{ item.date }}</td>
              <td>{{ item.time }}</td>
              <td class="id-cell">{{ item.borrower_id }}</td>
              <td class="id-cell">{{ item.bib_id }}</td>
              <td><span class="type-tag">{{ item.degree }}</span></td>
              <td><span class="category-tag">{{ item.category }}</span></td>
            </tr>
            <tr v-if="recentBorrows.length === 0" class="empty-row">
              <td colspan="6">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.borrows {
  max-width: var(--main-max-width);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  border: 1px solid var(--color-neutral-200);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-neutral-300);
  box-shadow: var(--shadow-lg);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  letter-spacing: var(--tracking-tight);
}

.stat-value .unit {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
}

.stat-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 10%, transparent) 0%, transparent 70%);
  border-radius: 50%;
  transition: opacity var(--transition-base);
}

.stat-card:hover .stat-glow {
  opacity: 1.5;
}

.card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  border: 1px solid var(--color-neutral-200);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-4);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-neutral-100);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.title-icon {
  width: 32px;
  height: 32px;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.title-icon svg {
  width: 16px;
  height: 16px;
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

.count-cell {
  font-weight: var(--font-semibold);
  color: var(--color-primary-600);
}

.count-cell .unit {
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
}

.id-cell {
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.percent-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.percent-fill {
  height: 6px;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 4px;
  flex: 1;
  max-width: 120px;
}

.percent-text {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-primary-500);
  min-width: 45px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: #fff;
  transition: transform var(--transition-fast);
}

.rank-badge:hover {
  transform: scale(1.1);
}

.rank-1 {
  background: var(--gradient-warm);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.rank-2 {
  background: linear-gradient(135deg, var(--color-neutral-400), var(--color-neutral-500));
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.3);
}

.rank-3 {
  background: linear-gradient(135deg, var(--color-warning-600), #92400e);
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.3);
}

.rank-4, .rank-5, .rank-6, .rank-7, .rank-8, .rank-9, .rank-10,
.rank-11, .rank-12, .rank-13, .rank-14, .rank-15 {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }

  .card {
    padding: var(--space-4);
  }

  .data-table th,
  .data-table td {
    padding: var(--space-2) var(--space-3);
    font-size: var(--text-xs);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .percent-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-1);
  }

  .percent-fill {
    max-width: 100%;
  }
}

.empty-row td {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
}
</style>