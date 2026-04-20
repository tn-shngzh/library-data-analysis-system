<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  preloadedData: {
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
const loading = ref(true)

const fetchReaderData = async () => {
  loading.value = true
  try {
    const [statsRes, typesRes, trendRes, topRes] = await Promise.all([
      fetch('/api/readers/stats'),
      fetch('/api/readers/types'),
      fetch('/api/readers/monthly-trend'),
      fetch('/api/readers/top')
    ])

    if (statsRes.ok) readerStats.value = await statsRes.json()
    if (typesRes.ok) readerTypes.value = await typesRes.json()
    if (trendRes.ok) monthlyTrend.value = await trendRes.json()
    if (topRes.ok) topReaders.value = await topRes.json()
  } catch (e) {
    console.error('获取数据失败', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.preloadedData, (data) => {
  if (data && data.stats) {
    readerStats.value = data.stats
    readerTypes.value = data.readerTypes || []
    monthlyTrend.value = data.monthlyTrend || []
    topReaders.value = data.topReaders || []
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (!props.preloadedData || !props.preloadedData.stats) {
    fetchReaderData()
  }
})

const formatNumber = (num) => num.toLocaleString()
</script>

<template>
  <div class="readers">
    <div class="page-header">
      <div class="header-content">
        <div>
          <h2>读者管理</h2>
          <p class="page-desc">读者数据统计与分析</p>
        </div>
        <div class="header-actions">
          <button class="refresh-btn" @click="fetchReaderData" :disabled="loading">
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
        <div class="stat-card" style="--accent: #6366f1">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">总读者数</span>
            <span class="stat-value">{{ formatNumber(readerStats.total_readers) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" style="--accent: #8b5cf6">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">本月活跃</span>
            <span class="stat-value">{{ formatNumber(readerStats.month_active) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" style="--accent: #06b6d4">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">本月借阅</span>
            <span class="stat-value">{{ formatNumber(readerStats.month_new) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" style="--accent: #10b981">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">平均借阅</span>
            <span class="stat-value">{{ readerStats.avg_borrows }} <span class="unit">本</span></span>
          </div>
          <div class="stat-glow"></div>
        </div>
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
            读者类型分布
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>读者类型</th>
              <th>人数</th>
              <th>占比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(type, index) in readerTypes" :key="type.name" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td><span class="type-tag">{{ type.name }}</span></td>
              <td class="count-cell">{{ formatNumber(type.count) }} <span class="unit">人</span></td>
              <td>
                <div class="percent-bar">
                  <div class="percent-fill" :style="{ width: type.percent + '%' }"></div>
                  <span class="percent-text">{{ type.percent }}%</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3v18h18"/>
                <path d="M18 17V9"/>
                <path d="M13 17V5"/>
                <path d="M8 17v-3"/>
              </svg>
            </span>
            月度活跃趋势
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>月份</th>
              <th>活跃人数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in monthlyTrend" :key="item.month" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td class="name-cell">{{ item.month }}</td>
              <td class="count-cell">{{ formatNumber(item.count) }} <span class="unit">人</span></td>
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
            活跃读者排行 TOP 10
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>排名</th>
              <th>读者ID</th>
              <th>类型</th>
              <th>借阅量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(reader, index) in topReaders" :key="reader.id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td>
                <span class="rank-badge" :class="'rank-' + reader.rank">{{ reader.rank }}</span>
              </td>
              <td class="id-cell">{{ reader.id }}</td>
              <td><span class="type-tag">{{ reader.type }}</span></td>
              <td class="count-cell">{{ formatNumber(reader.borrowed) }} <span class="unit">本</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.readers {
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

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.stat-value .unit {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
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

.card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(226, 232, 240, 0.6);
  margin-bottom: 18px;
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

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 14px 16px;
  font-size: 14px;
  color: #334155;
  border-bottom: 1px solid #f1f5f9;
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
  font-size: 12px;
  color: #6366f1;
  background: #eef2ff;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.count-cell {
  font-weight: 700;
  color: #6366f1;
}

.count-cell .unit {
  font-weight: 500;
  color: #64748b;
}

.id-cell {
  font-weight: 600;
  color: #0f172a;
}

.name-cell {
  font-weight: 500;
  color: #334155;
}

.percent-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.percent-fill {
  height: 8px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 4px;
}

.percent-text {
  font-size: 13px;
  font-weight: 600;
  color: #6366f1;
  min-width: 45px;
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
  color: #fff;
}

.rank-1 {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.rank-2 {
  background: linear-gradient(135deg, #94a3b8, #64748b);
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.3);
}

.rank-3 {
  background: linear-gradient(135deg, #d97706, #b45309);
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.3);
}

.rank-4, .rank-5, .rank-6, .rank-7, .rank-8, .rank-9, .rank-10 {
  background: #f1f5f9;
  color: #64748b;
}
</style>