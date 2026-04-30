<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookApi } from '@/api/books'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(true)
const activeTab = ref('category')
const categories = ref([])
const borrowByCategory = ref([])
const categoryTrend = ref([])

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const totalBooks = computed(() => categories.value.reduce((s, c) => s + (c.count || 0), 0))
const totalBorrows = computed(() => borrowByCategory.value.reduce((s, c) => s + (c.count || 0), 0))
const avgBorrowRate = computed(() => {
  if (totalBooks.value === 0) return '0%'
  return (totalBorrows.value / totalBooks.value * 100).toFixed(1) + '%'
})

const topCategory = computed(() => {
  if (!categories.value.length) return '-'
  return categories.value[0]?.name || '-'
})

const statCards = computed(() => [
  { i18nKey: 'category.categoryCount', value: categories.value.length, icon: 'layers', color: '#d97706' },
  { i18nKey: 'category.totalBooks', value: formatNumber(totalBooks.value), icon: 'book', color: '#3b82f6' },
  { i18nKey: 'category.totalBorrows', value: formatNumber(totalBorrows.value), icon: 'activity', color: '#10b981' },
  { i18nKey: 'category.topCategory', value: topCategory.value, icon: 'star', color: '#f59e0b' }
])

const fetchCategoryData = async () => {
  loading.value = true
  try {
    const bookData = await bookApi.getAll()
    if (bookData.categories) {
      categories.value = bookData.categories
      borrowByCategory.value = bookData.categories
    }
  } catch (e) {
    console.error('Failed to fetch category data', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.allData, (data) => {
  if (data) {
    if (data.books?.categories) {
      categories.value = data.books.categories
      borrowByCategory.value = data.books.categories
    }
    if (data.overview?.categories) {
      if (!categories.value.length) categories.value = data.overview.categories
    }
    loading.value = false
  }
}, { immediate: true, deep: true })

onMounted(() => {
  if (!props.allData || !props.allData.books?.categories) {
    fetchCategoryData()
  }
})

const maxCategoryCount = computed(() => {
  if (!categories.value.length) return 1
  return Math.max(...categories.value.map(c => c.count || 0))
})

const barColors = ['#d97706', '#fbbf24', '#a78bfa', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#3b82f6', '#059669', '#ef4444']
</script>

<template>
  <div class="category-view">
    <div class="page-header">
      <div class="header-info">
        <h1>{{ t('category.title') }}</h1>
        <p>{{ t('category.desc') }}</p>
      </div>
      <button class="refresh-btn btn btn-secondary btn-sm" @click="fetchCategoryData" :disabled="loading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M23 4v6h-6"/>
          <path d="M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        <span>{{ t('common.refresh') }}</span>
      </button>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>{{ t('common.loading') }}</span>
    </div>

    <template v-else>
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.i18nKey" class="stat-card" :style="{ '--accent': card.color }">
          <div class="stat-icon">
            <svg v-if="card.icon === 'layers'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"/>
              <polyline points="2 17 12 22 22 17"/>
              <polyline points="2 12 12 17 22 12"/>
            </svg>
            <svg v-else-if="card.icon === 'book'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            <svg v-else-if="card.icon === 'activity'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">{{ t(card.i18nKey) }}</span>
            <span class="stat-value">{{ card.value }}</span>
          </div>
        </div>
      </div>

      <div class="tab-bar">
        <button class="tab-btn btn-tab" :class="{ active: activeTab === 'category' }" @click="activeTab = 'category'">{{ t('category.categoryRatio') }}</button>
        <button class="tab-btn btn-tab" :class="{ active: activeTab === 'borrow' }" @click="activeTab = 'borrow'">{{ t('category.borrowAnalysis') }}</button>
      </div>

      <div v-if="activeTab === 'category'" class="card">
        <div class="card-header">
          <h3>{{ t('category.categoryRatio') }}</h3>
        </div>
        <div class="category-chart">
          <div class="bar-list">
            <div v-for="(cat, idx) in categories" :key="cat.name" class="bar-item">
              <div class="bar-label">
                <span class="bar-name">{{ cat.name }}</span>
                <span class="bar-value">{{ formatNumber(cat.count) }} ({{ cat.percent }}%)</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{
                    width: ((cat.count || 0) / maxCategoryCount * 100) + '%',
                    background: barColors[idx % barColors.length]
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'borrow'" class="card">
        <div class="card-header">
          <h3>{{ t('category.borrowAnalysis') }}</h3>
        </div>
        <div v-if="borrowByCategory.length" class="category-chart">
          <div class="bar-list">
            <div v-for="(item, idx) in borrowByCategory" :key="item.name" class="bar-item">
              <div class="bar-label">
                <span class="bar-name">{{ item.name }}</span>
                <span class="bar-value">{{ formatNumber(item.count) }} ({{ item.percent }}%)</span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{
                    width: (item.percent || 0) + '%',
                    background: barColors[idx % barColors.length]
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>{{ t('category.noData') }}</p>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>{{ t('category.detailList') }}</h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('category.rank') }}</th>
              <th>{{ t('category.name') }}</th>
              <th>{{ t('category.count') }}</th>
              <th>{{ t('category.percent') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(cat, idx) in categories" :key="cat.name">
              <td>
                <span class="rank-badge" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
              </td>
              <td class="name-cell">{{ cat.name }}</td>
              <td class="count-cell">{{ formatNumber(cat.count) }}</td>
              <td>
                <div class="percent-bar">
                  <div class="percent-fill" :style="{ width: cat.percent + '%' }"></div>
                  <span class="percent-text">{{ cat.percent }}%</span>
                </div>
              </td>
            </tr>
            <tr v-if="categories.length === 0" class="empty-row">
              <td colspan="4">{{ t('common.noData') }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.category-view {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.header-info p {
  font-size: 14px;
  color: var(--color-neutral-500);
  margin: 0;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: #94a3b8;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-neutral-0);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: 1px solid var(--color-neutral-200);
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--accent) 10%, var(--color-neutral-0));
  color: var(--accent);
  flex-shrink: 0;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 10px;
}

.tab-btn {
  flex: 1;
}

.card {
  background: var(--color-neutral-0);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid var(--color-neutral-200);
  margin-bottom: 16px;
}

.card-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.category-chart {
  padding: 8px 0;
}

.bar-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-name {
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.bar-value {
  font-size: 13px;
  color: var(--color-neutral-500);
}

.bar-track {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 4px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #94a3b8;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  border-bottom: 2px solid var(--color-neutral-200);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--color-neutral-600);
  border-bottom: 1px solid #f1f5f9;
}

.data-table tbody tr:hover td {
  background: var(--color-neutral-50);
}

.name-cell {
  font-weight: 600;
  color: #1e293b;
}

.count-cell {
  font-weight: 600;
  color: var(--color-primary-500);
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-neutral-0);
}

.rank-1 { background: linear-gradient(135deg, #f59e0b, var(--color-primary-500)); }
.rank-2 { background: linear-gradient(135deg, #94a3b8, var(--color-neutral-500)); }
.rank-3 { background: linear-gradient(135deg, var(--color-primary-500), #92400e); }
.rank-4, .rank-5, .rank-6, .rank-7, .rank-8, .rank-9, .rank-10 {
  background: #f1f5f9;
  color: var(--color-neutral-500);
}

.percent-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.percent-fill {
  height: 6px;
  background: linear-gradient(90deg, var(--color-primary-500), #fbbf24);
  border-radius: 3px;
  min-width: 4px;
  flex: 1;
  max-width: 120px;
  transition: width 0.5s ease;
}

.percent-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary-500);
  min-width: 45px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.empty-row td {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
}
</style>
