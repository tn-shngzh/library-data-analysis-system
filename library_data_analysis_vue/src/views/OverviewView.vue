<script setup>
import { ref, onMounted, watch } from 'vue'

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

const fetchOverviewData = async () => {
  loading.value = true
  try {
    const [statsRes, catRes, recentRes] = await Promise.all([
      fetch('/api/overview/stats'),
      fetch('/api/overview/categories'),
      fetch('/api/overview/recent-books')
    ])

    if (statsRes.ok) stats.value = await statsRes.json()
    if (catRes.ok) categories.value = await catRes.json()
    if (recentRes.ok) recentBooks.value = await recentRes.json()
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

const formatNumber = (num) => {
  return num.toLocaleString()
}

const actionMap = {
  'CKO': '借出',
  'CKI': '归还',
  'REH': '到馆续借',
  'REI': '网上续借'
}

const degreeMap = {
  '1a': '研究生', '1b': '本科', '1c': '大专', '1d': '高中',
  '1e': '初中', '1f': '小学', '1g': '临时', '1h': '学龄前'
}

const statCards = [
  { label: '总流通量', key: 'total_borrows', icon: 'book', accent: '#6366f1' },
  { label: '注册读者', key: 'total_readers', icon: 'users', accent: '#8b5cf6' },
  { label: '活跃读者', key: 'active_readers', icon: 'user-check', accent: '#06b6d4' },
  { label: '流通图书', key: 'total_books', icon: 'book-open', accent: '#10b981' },
  { label: '常规借书', key: 'cko_count', icon: 'arrow-up', accent: '#f59e0b' },
  { label: '归还', key: 'cki_count', icon: 'arrow-down', accent: '#ef4444' },
  { label: '到馆续借', key: 'reh_count', icon: 'refresh', accent: '#8b5cf6' },
  { label: '网上续借', key: 'rei_count', icon: 'wifi', accent: '#06b6d4' },
  { label: '今日到馆', key: 'today_visits', icon: 'calendar', accent: '#10b981' },
  { label: '图书分类', key: 'total_categories', icon: 'tag', accent: '#6366f1' }
]
</script>

<template>
  <div class="overview">
    <div class="page-header">
      <div class="header-content">
        <div>
          <h2>系统总览</h2>
          <p class="page-desc">图书馆运营数据概览</p>
        </div>
        <div class="header-actions">
          <button class="refresh-btn" @click="fetchOverviewData" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'spinning': loading }">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            <span>刷新</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>
    </div>
    <template v-else>
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
    </template>
  </div>
</template>

<style scoped>
.overview {
  max-width: 1280px;
}

.page-header {
  margin-bottom: 28px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 6px 0;
  letter-spacing: -0.02em;
}

.page-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.refresh-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #1e293b;
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

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  gap: 16px;
  color: #94a3b8;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(226, 232, 240, 0.6);
  position: relative;
  overflow: hidden;
  transition: all 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06), 0 8px 24px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--accent);
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 1;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stat-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 8%, transparent) 0%, transparent 70%);
  border-radius: 50%;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(226, 232, 240, 0.6);
}

.card-header {
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 8px;
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
  gap: 14px;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  animation: slideIn 0.3s ease backwards;
  animation-delay: var(--delay);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-name {
  font-size: 14px;
  color: #334155;
  font-weight: 500;
}

.category-count {
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
}

.category-count .unit {
  font-weight: 400;
  color: #94a3b8;
}

.category-bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.category-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.book-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  animation: slideIn 0.3s ease backwards;
  animation-delay: var(--delay);
  position: relative;
  overflow: hidden;
}

.book-item:hover {
  background: #f1f5f9;
  border-color: #e2e8f0;
}

.item-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  border-radius: 2px;
}

.book-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.book-author {
  font-size: 12px;
  color: #64748b;
}

.book-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.book-category {
  font-size: 11px;
  color: #6366f1;
  background: #eef2ff;
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.book-date {
  font-size: 12px;
  color: #94a3b8;
}
</style>
