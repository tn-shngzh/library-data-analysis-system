<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  allData: {
    type: Object,
    required: true
  }
})

const activeTrendTab = ref('月趋势')

const statsCards = [
  {
    key: 'total_flow',
    label: '总流通量',
    value: '6,232,387',
    change: '+12.5%',
    changeType: 'up',
    icon: 'book',
    color: '#6366f1'
  },
  {
    key: 'registered_readers',
    label: '注册读者',
    value: '102,235',
    change: '+8.2%',
    changeType: 'up',
    icon: 'users',
    color: '#3b82f6'
  },
  {
    key: 'active_readers',
    label: '活跃读者',
    value: '102,235',
    change: '+15.3%',
    changeType: 'up',
    icon: 'user-check',
    color: '#06b6d4'
  },
  {
    key: 'books_in_library',
    label: '在馆图书',
    value: '606,745',
    change: '+6.7%',
    changeType: 'up',
    icon: 'archive',
    color: '#10b981'
  },
  {
    key: 'borrowed_books',
    label: '借阅书',
    value: '2,359,385',
    change: '+10.1%',
    changeType: 'up',
    icon: 'arrow-up',
    color: '#f59e0b'
  },
  {
    key: 'returned_books',
    label: '归还图书',
    value: '2,343,205',
    change: '+9.3%',
    changeType: 'up',
    icon: 'arrow-down',
    color: '#ef4444'
  },
  {
    key: 'library_visits',
    label: '到馆借阅',
    value: '310,138',
    change: '+6.8%',
    changeType: 'up',
    icon: 'refresh',
    color: '#8b5cf6'
  },
  {
    key: 'online_renewals',
    label: '网上续借',
    value: '1,219,659',
    change: '+18.2%',
    changeType: 'up',
    icon: 'wifi',
    color: '#6366f1'
  }
]

const categoryData = [
  { name: '文学类', value: 2941788, percent: 40, color: '#818cf8' },
  { name: '社会科学类', value: 2091555, percent: 27, color: '#6366f1' },
  { name: '工程技术类', value: 1003566, percent: 13, color: '#a78bfa' },
  { name: '自然科学类', value: 618332, percent: 8, color: '#06b6d4' },
  { name: '人文类', value: 486657, percent: 6.3, color: '#10b981' },
  { name: '宗教类', value: 263728, percent: 3.4, color: '#f59e0b' },
  { name: '综合类', value: 313729, percent: 2.3, color: '#ec4899' }
]

const borrowTypeData = [
  { name: '文献借阅', percent: 38.1, color: '#6366f1' },
  { name: '社科借阅', percent: 26.8, color: '#818cf8' },
  { name: '科技借阅', percent: 13.3, color: '#06b6d4' },
  { name: '考研借阅', percent: 7.4, color: '#10b981' },
  { name: '人文借阅', percent: 6.3, color: '#f59e0b' },
  { name: '其他借阅', percent: 8.1, color: '#94a3b8' }
]

const topCategoriesData = [
  { rank: 1, name: '文学类', percent: 38.1, color: '#818cf8' },
  { rank: 2, name: '社会科学类', percent: 26.8, color: '#93c5fd' },
  { rank: 3, name: '工程技术类', percent: 13.3, color: '#c4b5fd' },
  { rank: 4, name: '经济类', percent: 7.4, color: '#a78bfa' },
  { rank: 5, name: '历史地理类', percent: 6.3, color: '#ddd6fe' },
  { rank: 6, name: '艺术类', percent: 3.8, color: '#ede9fe' },
  { rank: 7, name: '哲学宗教类', percent: 3.1, color: '#e0e7ff' },
  { rank: 8, name: '医药卫生类', percent: 2.6, color: '#dbeafe' },
  { rank: 9, name: '农业科学类', percent: 2.1, color: '#cffafe' },
  { rank: 10, name: '航空航天类', percent: 1.7, color: '#d1fae5' }
]

const trendData = [
  { month: '1月', value: 180 },
  { month: '2月', value: 220 },
  { month: '3月', value: 280 },
  { month: '4月', value: 250 },
  { month: '5月', value: 200 },
  { month: '6月', value: 240 },
  { month: '7月', value: 210 },
  { month: '8月', value: 300 },
  { month: '9月', value: 260 },
  { month: '10月', value: 290 },
  { month: '11月', value: 340 },
  { month: '12月', value: 380 }
]

const readerActivityData = [
  { name: '高活跃度（≥20次）', value: 24.5, color: '#06b6d4' },
  { name: '中活跃度（5-20次）', value: 41.2, color: '#8b5cf6' },
  { name: '低活跃度（1-5次）', value: 27.6, color: '#10b981' },
  { name: '沉寂用户（0次）', value: 6.7, color: '#ef4444' }
]

const todayStats = {
  visitors: '2,240 人',
  borrows: '1,835 册',
  returns: '1,523 部'
}

const formatNumber = (num) => {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
  const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  }
}

const describeArc = (x, y, radius, startAngle, endAngle) => {
  const start = polarToCartesian(x, y, radius, endAngle)
  const end = polarToCartesian(x, y, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  return ['M', start.x, start.y, 'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(' ')
}

const describeDonutArc = (x, y, innerRadius, outerRadius, startAngle, endAngle) => {
  const startOuter = polarToCartesian(x, y, outerRadius, endAngle)
  const endOuter = polarToCartesian(x, y, outerRadius, startAngle)
  const startInner = polarToCartesian(x, y, innerRadius, startAngle)
  const endInner = polarToCartesian(x, y, innerRadius, endAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  return [
    'M', startOuter.x, startOuter.y,
    'A', outerRadius, outerRadius, 0, largeArcFlag, 0, endOuter.x, endOuter.y,
    'L', startInner.x, startInner.y,
    'A', innerRadius, innerRadius, 0, largeArcFlag, 1, endInner.x, endInner.y,
    'Z'
  ].join(' ')
}

const getCategoryStartAngle = (index) => {
  let sum = 0
  for (let i = 0; i < index; i++) {
    sum += categoryData[i]?.percent || 0
  }
  return (sum / 100) * 360
}

const getCategoryEndAngle = (index) => {
  let sum = 0
  for (let i = 0; i <= index; i++) {
    sum += categoryData[i]?.percent || 0
  }
  return (sum / 100) * 360
}

const getBorrowTypeStartAngle = (index) => {
  let sum = 0
  for (let i = 0; i < index; i++) {
    sum += borrowTypeData[i]?.percent || 0
  }
  return (sum / 100) * 360
}

const getBorrowTypeEndAngle = (index) => {
  let sum = 0
  for (let i = 0; i <= index; i++) {
    sum += borrowTypeData[i]?.percent || 0
  }
  return (sum / 100) * 360
}

const getReaderActivityStartAngle = (index) => {
  let sum = 0
  for (let i = 0; i < index; i++) {
    sum += readerActivityData[i]?.value || 0
  }
  return (sum / 100) * 360
}

const getReaderActivityEndAngle = (index) => {
  let sum = 0
  for (let i = 0; i <= index; i++) {
    sum += readerActivityData[i]?.value || 0
  }
  return (sum / 100) * 360
}

const maxTrendValue = computed(() => Math.max(...trendData.map(d => d.value)))
const minTrendValue = computed(() => Math.min(...trendData.map(d => d.value)))

const generateTrendPath = () => {
  const width = 800
  const height = 280
  const padding = 40
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2

  const points = trendData.map((d, i) => ({
    x: padding + (i / (trendData.length - 1)) * chartWidth,
    y: padding + chartHeight - ((d.value - minTrendValue.value) / (maxTrendValue.value - minTrendValue.value)) * chartHeight
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  const areaPath = linePath +
    ` L ${points[points.length - 1].x} ${padding + chartHeight}` +
    ` L ${points[0].x} ${padding + chartHeight} Z`

  return { linePath, areaPath, points }
}

const trendPaths = generateTrendPath()
</script>

<template>
  <div class="overview-container">
    <!-- Stats Cards Row -->
    <div class="stats-cards-grid">
      <div
        v-for="(card, index) in statsCards"
        :key="card.key"
        class="stat-card"
        :style="{ '--card-color': card.color }"
      >
        <div class="stat-icon-wrapper">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="stat-icon">
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
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">{{ card.label }}</span>
          <span class="stat-value">{{ card.value }}</span>
          <div class="stat-change" :class="card.changeType">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-if="card.changeType === 'up'" class="change-icon">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
            <span>较去年 {{ card.change }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row 1 -->
    <div class="charts-row">
      <!-- Category Distribution Pie Chart -->
      <div class="chart-card pie-chart-card">
        <h3 class="chart-title">借阅分类分布</h3>
        <div class="chart-content">
          <svg viewBox="0 0 320 260" class="pie-svg">
            <g transform="translate(130, 130)">
              <path
                v-for="(item, idx) in categoryData"
                :key="idx"
                :d="describeArc(0, 0, 95, getCategoryStartAngle(idx), getCategoryEndAngle(idx))"
                :fill="item.color"
                stroke="#fff"
                stroke-width="2"
                class="pie-slice"
              />
              <circle cx="0" cy="0" r="50" fill="white"/>
              <text x="0" y="-8" text-anchor="middle" font-size="22" font-weight="700" fill="#1e293b">{{ formatNumber(7719745) }}</text>
              <text x="0" y="14" text-anchor="middle" font-size="11" fill="#64748b">分类总借阅量</text>
            </g>
          </svg>
          <div class="pie-legend">
            <div v-for="(item, idx) in categoryData" :key="idx" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-percent">{{ item.percent }}%</span>
              <span class="legend-value">{{ formatNumber(item.value) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Borrow Type Donut Chart -->
      <div class="chart-card donut-chart-card">
        <h3 class="chart-title">借阅类型占比</h3>
        <div class="chart-content donut-content">
          <svg viewBox="0 0 220 220" class="donut-svg">
            <g transform="translate(110, 110)">
              <path
                v-for="(item, idx) in borrowTypeData"
                :key="idx"
                :d="describeDonutArc(0, 0, 65, 90, getBorrowTypeStartAngle(idx), getBorrowTypeEndAngle(idx))"
                :fill="item.color"
                class="donut-slice"
              />
              <text x="0" y="-5" text-anchor="middle" font-size="28" font-weight="700" fill="#1e293b">38.1%</text>
              <text x="0" y="16" text-anchor="middle" font-size="12" fill="#64748b">文学类占比</text>
            </g>
          </svg>
          <div class="donut-legend">
            <div v-for="(item, idx) in borrowTypeData" :key="idx" class="legend-item-small">
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-value">{{ item.percent }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Top 10 Categories Bar Chart -->
      <div class="chart-card bar-chart-card">
        <h3 class="chart-title">Top 10 借阅分类占比</h3>
        <div class="chart-content bar-content">
          <div v-for="(item, idx) in topCategoriesData" :key="idx" class="bar-item">
            <div class="bar-rank" :class="{ 'top-3': item.rank <= 3 }">{{ item.rank }}</div>
            <span class="bar-name">{{ item.name }}</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: item.percent + '%', background: item.color }"></div>
            </div>
            <span class="bar-value">{{ item.percent }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Row 2 -->
    <div class="charts-row charts-row-main">
      <!-- Trend Line Chart -->
      <div class="chart-card trend-chart-card">
        <div class="trend-header">
          <h3 class="chart-title">借阅趋势分析</h3>
          <div class="trend-tabs">
            <button
              v-for="tab in ['日趋势', '周趋势', '月趋势', '年趋势']"
              :key="tab"
              class="trend-tab"
              :class="{ active: activeTrendTab === tab }"
              @click="activeTrendTab = tab"
            >{{ tab }}</button>
          </div>
          <div class="year-selector">
            <span>2026年</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>
        <div class="chart-content trend-content">
          <svg viewBox="0 0 800 280" class="trend-svg">
            <defs>
              <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#818cf8;stop-opacity:0.3" />
                <stop offset="100%" style="stop-color:#818cf8;stop-opacity:0.02" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            <path :d="trendPaths.areaPath" fill="url(#areaGradient)" />

            <path :d="trendPaths.linePath" fill="none" stroke="#6366f1" stroke-width="3" filter="url(#glow)" stroke-linecap="round" stroke-linejoin="round"/>

            <g v-for="(point, idx) in trendPaths.points" :key="idx">
              <circle :cx="point.cx" :cy="point.cy" r="5" fill="white" stroke="#6366f1" stroke-width="2" class="data-point"/>
              <text :x="point.cx" :y="point.cy - 12" text-anchor="middle" font-size="10" fill="#64748b" v-if="idx % 2 === 0">{{ trendData[idx].value }}万</text>
            </g>

            <g v-for="(item, idx) in trendData" :key="'label-' + idx">
              <text :x="40 + (idx / (trendData.length - 1)) * 720" y="270" text-anchor="middle" font-size="11" fill="#94a3b8">{{ item.month }}</text>
            </g>

            <g class="tooltip-group" transform="translate(420, 140)">
              <rect x="-60" y="-45" width="120" height="55" rx="8" fill="white" filter="url(#shadow)" opacity="0.95"/>
              <text x="0" y="-25" text-anchor="middle" font-size="11" fill="#64748b">6月借阅量</text>
              <text x="0" y="-5" text-anchor="middle" font-size="16" font-weight="700" fill="#1e293b">425,692 册</text>
            </g>
          </svg>
        </div>
      </div>

      <!-- Reader Activity & Today Summary -->
      <div class="right-column">
        <!-- Reader Activity Donut -->
        <div class="chart-card activity-chart-card">
          <h3 class="chart-title">读者活跃度分布</h3>
          <div class="chart-content activity-content">
            <svg viewBox="0 0 200 200" class="activity-donut-svg">
              <g transform="translate(100, 100)">
                <path
                  v-for="(item, idx) in readerActivityData"
                  :key="idx"
                  :d="describeDonutArc(0, 0, 60, 78, getReaderActivityStartAngle(idx), getReaderActivityEndAngle(idx))"
                  :fill="item.color"
                  class="activity-slice"
                />
                <text x="0" y="-5" text-anchor="middle" font-size="22" font-weight="700" fill="#1e293b">102,235</text>
                <text x="0" y="14" text-anchor="middle" font-size="10" fill="#64748b">读者总数</text>
              </g>
            </svg>
            <div class="activity-legend">
              <div v-for="(item, idx) in readerActivityData" :key="idx" class="legend-item-tiny">
                <span class="legend-dot" :style="{ background: item.color }"></span>
                <span class="legend-name">{{ item.name }}</span>
                <span class="legend-value">{{ item.value }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Today Summary Card -->
        <div class="today-summary-card">
          <h3 class="today-title">今日概况</h3>
          <div class="today-mini-chart">
            <svg viewBox="0 0 200 80" class="mini-line-chart">
              <polyline
                points="0,60 20,45 40,55 60,30 80,40 100,25 120,35 140,20 160,30 180,15 200,25"
                fill="none"
                stroke="#818cf8"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <div class="today-stats-list">
            <div class="today-stat-item">
              <span class="today-label">今日到馆</span>
              <span class="today-value">{{ todayStats.visitors }}</span>
            </div>
            <div class="today-stat-item">
              <span class="today-label">今日借书</span>
              <span class="today-value">{{ todayStats.borrows }}</span>
            </div>
            <div class="today-stat-item">
              <span class="today-label">今日还书</span>
              <span class="today-value">{{ todayStats.returns }}</span>
            </div>
          </div>
          <div class="version-tag">v1.0.0</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="./OverviewView.css"></style>
