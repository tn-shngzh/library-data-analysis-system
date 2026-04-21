<script setup>
import { ref, onMounted, watch } from 'vue'
import { overviewApi } from '@/api/overview'
import { formatNumber } from '@/utils/format'
import { getCache, setCache, clearCache } from '@/utils/cache'
import { STAT_CARDS_CONFIG, ACTION_MAP, DEGREE_MAP } from '@/constants'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import CategoryList from '@/components/CategoryList.vue'

const CACHE_KEY = 'overviewData'
const CACHE_TTL = 5 * 60 * 1000

const props = defineProps({
  preloadedData: {
    type: Object,
    default: null
  }
})

const stats = ref({
  total_readers: 0,
  total_borrows: 0,
  active_readers: 0,
  total_books: 0,
  cko_count: 0,
  cki_count: 0,
  reh_count: 0,
  rei_count: 0,
  today_visits: 0,
  total_categories: 0
})

const categories = ref([])
const recentBooks = ref([])
const loading = ref(true)

const fetchOverviewData = async (forceRefresh = false) => {
  loading.value = true
  
  if (!forceRefresh) {
    const cached = getCache(CACHE_KEY)
    if (cached) {
      stats.value = cached.stats || stats.value
      categories.value = cached.categories || []
      recentBooks.value = cached.recentBooks || []
      loading.value = false
      return
    }
  } else {
    clearCache(CACHE_KEY)
  }
  
  try {
    const data = await overviewApi.getAll()
    if (data.stats) stats.value = data.stats
    if (data.categories) categories.value = data.categories
    if (data.recentBooks) recentBooks.value = data.recentBooks
    setCache(CACHE_KEY, {
      stats: stats.value,
      categories: categories.value,
      recentBooks: recentBooks.value
    }, CACHE_TTL)
  } catch (e) {
    console.error('获取数据失败', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.preloadedData, (data) => {
  if (data && data.stats) {
    stats.value = data.stats
    categories.value = data.categories || []
    recentBooks.value = data.recentBooks || []
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (!props.preloadedData || !props.preloadedData.stats) {
    fetchOverviewData()
  }
})

const handleRefresh = () => {
  fetchOverviewData(true)
}

const statCards = STAT_CARDS_CONFIG
</script>

<template>
  <div class="overview">
    <PageHeader title="系统总览" description="图书馆运营数据概览" :loading="loading" @refresh="handleRefresh" />

    <LoadingSpinner :loading="loading">
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.key" class="stat-card" :style="{ '--accent': card.accent }">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
              <template v-else-if="card.icon === 'book-open'">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
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
              <template v-else-if="card.icon === 'calendar'">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </template>
              <template v-else-if="card.icon === 'map'">
                <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/>
                <line x1="8" y1="2" x2="8" y2="18"/>
                <line x1="16" y1="6" x2="16" y2="22"/>
              </template>
              <template v-else-if="card.icon === 'tag'">
                <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                <line x1="7" y1="7" x2="7.01" y2="7"/>
              </template>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ formatNumber(stats[card.key]) }}</span>
            <span class="stat-label">{{ card.label }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>
      </div>

      <div class="content-grid">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                  <line x1="7" y1="7" x2="7.01" y2="7"/>
                </svg>
              </span>
              图书分类
            </h3>
          </div>
          <CategoryList :items="categories" nameKey="category" />
        </div>

        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="title-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
              </span>
              最近入库图书
            </h3>
          </div>
          <div class="book-list">
            <div v-for="(book, index) in recentBooks" :key="book.bib_id" class="book-item" :style="{ '--delay': `${index * 0.05}s` }">
              <div class="item-indicator"></div>
              <div class="book-info">
                <span class="book-title">{{ book.name }}</span>
                <span class="book-author">{{ book.author }}</span>
              </div>
              <div class="book-meta">
                <span class="book-category">{{ book.category }}</span>
                <span class="book-date">{{ book.date }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.overview {
  max-width: 1280px;
}

.page-header {
  margin-bottom: var(--space-7);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: var(--tracking-tight);
}

.page-desc {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-neutral-0);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.refresh-btn:hover {
  background: var(--color-neutral-50);
  border-color: var(--color-neutral-300);
  color: var(--color-neutral-900);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  color: var(--color-neutral-500);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
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
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--accent);
}

.stat-icon svg {
  width: 22px;
  height: 22px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 1;
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  letter-spacing: var(--tracking-tight);
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.stat-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 10%, transparent) 0%, transparent 70%);
  border-radius: 50%;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: var(--shadow-sm);
}

.card-header {
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.title-icon {
  width: 28px;
  height: 28px;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.title-icon svg {
  width: 16px;
  height: 16px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  animation: slideInLeft 0.3s ease backwards;
  animation-delay: var(--delay);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-name {
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
  font-weight: var(--font-medium);
}

.category-count {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-semibold);
}

.category-count .unit {
  font-weight: var(--font-regular);
  color: var(--color-neutral-500);
}

.category-bar {
  height: 6px;
  background: var(--color-neutral-100);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.category-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.book-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  transition: all var(--transition-base);
  animation: slideInLeft 0.3s ease backwards;
  animation-delay: var(--delay);
  position: relative;
  overflow: hidden;
}

.book-item:hover {
  background: var(--color-neutral-100);
  border-color: var(--color-neutral-200);
}

.item-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--gradient-primary);
  border-radius: 2px;
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.book-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.book-author {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.book-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-1);
}

.book-category {
  font-size: var(--text-xs);
  color: var(--color-primary-400);
  background: var(--color-primary-50);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-weight: var(--font-medium);
}

.book-date {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .card {
    padding: var(--space-4);
  }

  .book-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }

  .book-meta {
    flex-direction: row;
    align-items: center;
    gap: var(--space-2);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .stat-card {
    padding: var(--space-4);
  }
}
</style>
