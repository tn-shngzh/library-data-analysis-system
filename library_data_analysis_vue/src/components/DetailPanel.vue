<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { formatNumber } from '@/utils/format'
import { exportToCSV, exportToPDF, formatDate } from '@/utils/export'
import { getCache, setCache } from '@/utils/cache'

const props = defineProps({
  cardKey: { type: String, required: true },
  cardLabel: { type: String, required: true },
  accent: { type: String, default: '#6366f1' },
  data: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref(null)
const sortBy = ref('value')
const sortOrder = ref('desc')
const filterText = ref('')
const timeRange = ref('all')
const detailData = ref(null)
const activeTab = ref('overview')

const timeRangeOptions = [
  { value: 'all', label: '全部' },
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' }
]

const tabOptions = computed(() => {
  const tabs = [{ id: 'overview', label: '概览' }]
  if (hasTrendData.value) tabs.push({ id: 'trend', label: '趋势' })
  if (hasComparison.value) tabs.push({ id: 'comparison', label: '对比' })
  return tabs
})

const hasTrendData = computed(() => {
  return props.data?.monthlyTrend?.length > 0 || props.data?.trend?.length > 0
})

const hasComparison = computed(() => {
  return props.data?.comparison || props.data?.degreeStats?.length > 0 || props.data?.actionStats?.length > 0
})

const filteredData = computed(() => {
  let data = detailData.value || []

  if (filterText.value) {
    const search = filterText.value.toLowerCase()
    data = data.filter(item =>
      Object.values(item).some(v =>
        String(v).toLowerCase().includes(search)
      )
    )
  }

  if (sortBy.value && data.length) {
    data = [...data].sort((a, b) => {
      const aVal = a[sortBy.value] ?? 0
      const bVal = b[sortBy.value] ?? 0
      return sortOrder.value === 'desc' ? bVal - aVal : aVal - bVal
    })
  }

  return data
})

const trendData = computed(() => {
  return props.data?.monthlyTrend || props.data?.trend || []
})

const maxTrendValue = computed(() => {
  if (!trendData.value.length) return 1
  return Math.max(...trendData.value.map(t => t.count || t.value || 0))
})

const loadData = async () => {
  const cacheKey = `detail_${props.cardKey}`
  const cached = getCache(cacheKey, 5 * 60 * 1000)

  if (cached) {
    detailData.value = cached
    return
  }

  loading.value = true
  error.value = null

  try {
    await new Promise(resolve => setTimeout(resolve, 300))

    const data = prepareDetailData()
    detailData.value = data
    setCache(cacheKey, data)
  } catch (e) {
    error.value = '加载数据失败，请稍后重试'
    console.error('Load detail data error:', e)
  } finally {
    loading.value = false
  }
}

const prepareDetailData = () => {
  const d = props.data

  switch (props.cardKey) {
    case 'total_readers':
      return d.readerTypes?.map(t => ({
        name: t.name,
        value: t.count,
        percent: t.percent
      })) || []

    case 'active_readers':
      return d.topReaders?.map(r => ({
        rank: r.rank,
        name: `读者 #${r.id}`,
        value: r.borrowed
      })) || []

    case 'total_borrows':
      return d.actionStats?.map(a => ({
        name: a.name || a.action,
        value: a.count,
        percent: a.percent
      })) || []

    case 'total_books':
      return d.hotBooks?.map(b => ({
        rank: b.rank,
        name: b.name,
        category: b.category,
        value: b.borrow_count
      })) || []

    case 'total_categories':
      return d.categories?.map(c => ({
        name: c.name,
        value: c.count,
        percent: c.percent
      })) || []

    case 'cko_count':
    case 'cki_count':
    case 'rei_count':
      return d.topBorrowers?.map(b => ({
        rank: b.rank,
        name: `读者 #${b.borrower_id}`,
        degree: b.degree,
        value: b.borrow_count
      })) || []

    case 'reh_count':
      return d.topBooks?.map(b => ({
        rank: b.rank,
        name: b.category,
        value: b.borrow_count
      })) || []

    case 'today_visits':
      return d.recentBorrows?.map(r => ({
        name: r.title || '未知图书',
        degree: r.degree,
        date: r.date
      })) || []

    default:
      return []
  }
}

const handleExportCSV = () => {
  const headers = getExportHeaders()
  exportToCSV(filteredData.value, `${props.cardLabel}_数据导出_${formatDate(new Date())}`, headers)
}

const handleExportPDF = () => {
  exportToPDF('detail-content', `${props.cardLabel}_数据报告`)
}

const getExportHeaders = () => {
  const baseHeaders = {
    name: '名称',
    value: '数值',
    percent: '百分比',
    rank: '排名',
    category: '分类',
    degree: '学历',
    date: '日期'
  }
  return baseHeaders
}

const toggleSort = (field) => {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortBy.value = field
    sortOrder.value = 'desc'
  }
}

const getTrendBarHeight = (item) => {
  const val = item.count || item.value || 0
  return Math.max(4, (val / maxTrendValue.value) * 100)
}

watch(() => props.cardKey, () => {
  loadData()
}, { immediate: true })

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="detail-panel" :style="{ '--accent': accent }">
    <div class="detail-header">
      <div class="header-left">
        <h3>{{ cardLabel }}详情</h3>
        <div class="breadcrumb">
          <span class="breadcrumb-item">总览</span>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-item active">{{ cardLabel }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="handleExportCSV" title="导出CSV">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>CSV</span>
        </button>
        <button class="action-btn" @click="handleExportPDF" title="导出PDF">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <span>PDF</span>
        </button>
        <button class="close-btn" @click="$emit('close')" title="关闭">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="detail-tabs" v-if="tabOptions.length > 1">
      <button
        v-for="tab in tabOptions"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="detail-toolbar">
      <div class="search-box">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="filterText"
          type="text"
          placeholder="搜索..."
          class="search-input"
        />
      </div>
      <div class="time-filter">
        <select v-model="timeRange" class="time-select">
          <option v-for="opt in timeRangeOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>
    </div>

    <div id="detail-content" class="detail-body">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span>正在加载数据...</span>
      </div>

      <div v-else-if="error" class="error-state">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>{{ error }}</span>
        <button class="retry-btn" @click="loadData">重试</button>
      </div>

      <template v-else>
        <div v-if="activeTab === 'trend'" class="trend-view">
          <h4 class="section-title">趋势分析</h4>
          <div class="trend-chart">
            <div class="trend-bars">
              <div v-for="(item, idx) in trendData" :key="idx" class="trend-column">
                <div class="trend-bar-wrapper">
                  <div
                    class="trend-bar"
                    :style="{ height: getTrendBarHeight(item) + '%' }"
                  >
                    <span class="bar-value">{{ formatNumber(item.count || item.value) }}</span>
                  </div>
                </div>
                <span class="trend-label">{{ item.month || item.label }}</span>
              </div>
            </div>
          </div>
          <div class="trend-stats">
            <div class="trend-stat">
              <span class="stat-label">最高值</span>
              <span class="stat-value">{{ formatNumber(maxTrendValue) }}</span>
            </div>
            <div class="trend-stat">
              <span class="stat-label">平均值</span>
              <span class="stat-value">{{ formatNumber(Math.round(trendData.reduce((a, b) => a + (b.count || b.value || 0), 0) / trendData.length)) }}</span>
            </div>
            <div class="trend-stat">
              <span class="stat-label">数据点</span>
              <span class="stat-value">{{ trendData.length }}</span>
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'comparison'" class="comparison-view">
          <h4 class="section-title">对比分析</h4>
          <div class="comparison-chart">
            <svg viewBox="0 0 400 200" class="pie-chart" v-if="filteredData.length">
              <g transform="translate(100, 100)">
                <path
                  v-for="(item, idx) in filteredData.slice(0, 8)"
                  :key="idx"
                  :d="describeArc(0, 0, 80, getStartAngle(idx), getEndAngle(idx))"
                  :fill="getColor(idx)"
                  stroke="white"
                  stroke-width="2"
                />
              </g>
              <g transform="translate(220, 20)">
                <g v-for="(item, idx) in filteredData.slice(0, 8)" :key="idx" :transform="`translate(0, ${idx * 22})`">
                  <rect width="12" height="12" :fill="getColor(idx)" rx="2"/>
                  <text x="18" y="10" font-size="11" fill="#374151">{{ item.name?.slice(0, 10) }}</text>
                  <text x="150" y="10" font-size="11" fill="#6B7280" text-anchor="end">{{ item.percent || '' }}%</text>
                </g>
              </g>
            </svg>
          </div>
        </div>

        <div v-else class="overview-view">
          <div class="data-table">
            <div class="table-header">
              <div class="th" @click="toggleSort('rank')" v-if="filteredData[0]?.rank !== undefined">
                排名
                <svg v-if="sortBy === 'rank'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: sortOrder === 'asc' }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div class="th" @click="toggleSort('name')">
                名称
                <svg v-if="sortBy === 'name'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: sortOrder === 'asc' }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div class="th" @click="toggleSort('value')">
                数值
                <svg v-if="sortBy === 'value'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: sortOrder === 'asc' }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div class="th" v-if="filteredData[0]?.percent !== undefined">占比</div>
            </div>
            <div class="table-body">
              <div
                v-for="(item, idx) in filteredData"
                :key="idx"
                class="table-row"
              >
                <div class="td" v-if="item.rank !== undefined">
                  <span class="rank-badge">{{ item.rank }}</span>
                </div>
                <div class="td name-cell">
                  {{ item.name }}
                  <span v-if="item.category" class="cell-badge">{{ item.category }}</span>
                  <span v-if="item.degree" class="cell-badge">{{ item.degree }}</span>
                </div>
                <div class="td">
                  <span class="value-text">{{ formatNumber(item.value) }}</span>
                  <div v-if="item.percent !== undefined" class="mini-bar-wrapper">
                    <div class="mini-bar" :style="{ width: item.percent + '%' }"></div>
                  </div>
                </div>
                <div class="td" v-if="item.percent !== undefined">
                  {{ item.percent }}%
                </div>
                <div class="td" v-if="item.date">
                  {{ item.date }}
                </div>
              </div>
            </div>
          </div>

          <div class="data-summary">
            <div class="summary-item">
              <span class="summary-label">总计</span>
              <span class="summary-value">{{ filteredData.length }} 条记录</span>
            </div>
            <div class="summary-item" v-if="filteredData[0]?.value !== undefined">
              <span class="summary-label">合计</span>
              <span class="summary-value">{{ formatNumber(filteredData.reduce((a, b) => a + (b.value || 0), 0)) }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script>
const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#64748b']

export default {
  methods: {
    getColor(index) {
      return COLORS[index % COLORS.length]
    },
    describeArc(x, y, radius, startAngle, endAngle) {
      const start = this.polarToCartesian(x, y, radius, endAngle)
      const end = this.polarToCartesian(x, y, radius, startAngle)
      const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
      return [
        'M', start.x, start.y,
        'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y,
        'L', x, y,
        'Z'
      ].join(' ')
    },
    polarToCartesian(centerX, centerY, radius, angleInDegrees) {
      const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
      return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
      }
    },
    getStartAngle(index) {
      const total = this.filteredData.reduce((a, b) => a + (b.value || b.percent || 0), 0)
      let sum = 0
      for (let i = 0; i < index; i++) {
        sum += (this.filteredData[i]?.value || this.filteredData[i]?.percent || 0) / total * 360
      }
      return sum
    },
    getEndAngle(index) {
      const total = this.filteredData.reduce((a, b) => a + (b.value || b.percent || 0), 0)
      let sum = 0
      for (let i = 0; i <= index; i++) {
        sum += (this.filteredData[i]?.value || this.filteredData[i]?.percent || 0) / total * 360
      }
      return sum
    }
  },
  computed: {
    filteredData() {
      return this.$options.parent.filteredData
    }
  }
}
</script>

<style scoped>
.detail-panel {
  background: var(--color-neutral-0);
  border: 1px solid var(--accent);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  border-bottom: 1px solid var(--color-neutral-100);
}

.header-left h3 {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-1) 0;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
}

.breadcrumb-item {
  color: var(--color-neutral-500);
}

.breadcrumb-item.active {
  color: var(--accent);
  font-weight: var(--font-medium);
}

.breadcrumb-sep {
  color: var(--color-neutral-300);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: var(--color-neutral-0);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--color-neutral-600);
  cursor: pointer;
  transition: all var(--transition-base);
}

.action-btn:hover {
  background: var(--color-neutral-50);
  border-color: var(--accent);
  color: var(--accent);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.close-btn {
  width: 32px;
  height: 32px;
  background: var(--color-neutral-100);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-neutral-500);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
}

.close-btn:hover {
  background: var(--color-danger-50);
  color: var(--color-danger-500);
}

.close-btn svg {
  width: 16px;
  height: 16px;
}

.detail-tabs {
  display: flex;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-neutral-100);
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
  cursor: pointer;
  transition: all var(--transition-base);
}

.tab-btn:hover {
  background: var(--color-neutral-100);
  color: var(--color-neutral-700);
}

.tab-btn.active {
  background: var(--accent);
  color: white;
}

.detail-toolbar {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  background: var(--color-neutral-50);
  border-bottom: 1px solid var(--color-neutral-100);
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-neutral-0);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
}

.search-box svg {
  width: 16px;
  height: 16px;
  color: var(--color-neutral-400);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: var(--text-sm);
  background: transparent;
}

.time-select {
  padding: var(--space-2) var(--space-3);
  background: var(--color-neutral-0);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
}

.detail-body {
  padding: var(--space-5);
  max-height: 500px;
  overflow-y: auto;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-10);
  gap: var(--space-3);
  color: var(--color-neutral-500);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state svg {
  width: 32px;
  height: 32px;
  color: var(--color-danger-400);
}

.retry-btn {
  margin-top: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-base);
}

.retry-btn:hover {
  opacity: 0.9;
}

.section-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-700);
  margin: 0 0 var(--space-4) 0;
}

.trend-chart {
  margin-bottom: var(--space-5);
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  gap: var(--space-2);
  height: 160px;
  padding: var(--space-3) 0;
}

.trend-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.trend-bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.trend-bar {
  width: 100%;
  max-width: 40px;
  background: linear-gradient(180deg, var(--accent), color-mix(in srgb, var(--accent) 70%, transparent));
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  position: relative;
  transition: height 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.bar-value {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--color-neutral-600);
  white-space: nowrap;
}

.trend-label {
  font-size: 10px;
  color: var(--color-neutral-500);
  margin-top: var(--space-1);
  white-space: nowrap;
}

.trend-stats {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
}

.trend-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trend-stat .stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.trend-stat .stat-value {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.comparison-chart {
  display: flex;
  justify-content: center;
}

.pie-chart {
  width: 100%;
  max-width: 400px;
  height: auto;
}

.data-table {
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.table-header {
  display: flex;
  background: var(--color-neutral-50);
  border-bottom: 1px solid var(--color-neutral-200);
}

.th {
  flex: 1;
  padding: var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-600);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--space-1);
  transition: color var(--transition-base);
}

.th:hover {
  color: var(--accent);
}

.th svg {
  width: 12px;
  height: 12px;
  transition: transform var(--transition-base);
}

.th svg.rotated {
  transform: rotate(180deg);
}

.table-body {
  max-height: 300px;
  overflow-y: auto;
}

.table-row {
  display: flex;
  border-bottom: 1px solid var(--color-neutral-100);
  transition: background var(--transition-base);
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: var(--color-neutral-50);
}

.td {
  flex: 1;
  padding: var(--space-3);
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.name-cell {
  font-weight: var(--font-medium);
}

.rank-badge {
  width: 24px;
  height: 24px;
  background: var(--gradient-primary);
  color: white;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.cell-badge {
  font-size: var(--text-xs);
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
}

.value-text {
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.mini-bar-wrapper {
  flex: 1;
  max-width: 80px;
  height: 4px;
  background: var(--color-neutral-200);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.mini-bar {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.data-summary {
  display: flex;
  gap: var(--space-4);
  margin-top: var(--space-4);
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.summary-value {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .detail-toolbar {
    flex-direction: column;
  }

  .trend-bars {
    height: 120px;
  }

  .bar-value {
    display: none;
  }
}
</style>
