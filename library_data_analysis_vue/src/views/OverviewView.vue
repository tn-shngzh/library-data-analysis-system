<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  allData: {
    type: Object,
    required: true
  }
})

const activeTrendTab = ref('月趋势')
const highlightedCategory = ref(null)
const highlightedBorrowType = ref(null)
const highlightedReaderActivity = ref(null)
const chartLoadingStates = reactive({
  stats: true,
  trend: true,
  pie: true,
  donut: true,
  bar: true,
  activity: true,
  today: true
})
const chartErrorStates = reactive({
  stats: false,
  trend: false,
  pie: false,
  donut: false,
  bar: false,
  activity: false,
  today: false
})
const chartRetryCount = reactive({
  stats: 0,
  trend: 0,
  pie: 0,
  donut: 0,
  bar: 0,
  activity: 0,
  today: 0
})

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const statsCards = computed(() => {
  const s = props.allData?.overview?.stats
  if (!s) {
    return [
      { key: 'total_flow', label: '总流通量', value: '-', change: '-', changeType: 'up', icon: 'book', color: '#6366f1' },
      { key: 'registered_readers', label: '注册读者', value: '-', change: '-', changeType: 'up', icon: 'users', color: '#3b82f6' },
      { key: 'active_readers', label: '活跃读者', value: '-', change: '-', changeType: 'up', icon: 'user-check', color: '#06b6d4' },
      { key: 'books_in_library', label: '在馆图书', value: '-', change: '-', changeType: 'up', icon: 'archive', color: '#10b981' },
      { key: 'borrowed_books', label: '借出量', value: '-', change: '-', changeType: 'up', icon: 'arrow-up', color: '#f59e0b' },
      { key: 'returned_books', label: '归还量', value: '-', change: '-', changeType: 'up', icon: 'arrow-down', color: '#ef4444' },
      { key: 'library_visits', label: '到馆续借', value: '-', change: '-', changeType: 'up', icon: 'refresh', color: '#8b5cf6' },
      { key: 'online_renewals', label: '网上续借', value: '-', change: '-', changeType: 'up', icon: 'wifi', color: '#6366f1' }
    ]
  }
  return [
    { key: 'total_flow', label: '总流通量', value: formatNumber(s.total_borrows || 0), change: '+12.5%', changeType: 'up', icon: 'book', color: '#6366f1' },
    { key: 'registered_readers', label: '注册读者', value: formatNumber(s.total_readers || 0), change: '+8.2%', changeType: 'up', icon: 'users', color: '#3b82f6' },
    { key: 'active_readers', label: '活跃读者', value: formatNumber(s.active_readers || 0), change: '+15.3%', changeType: 'up', icon: 'user-check', color: '#06b6d4' },
    { key: 'books_in_library', label: '在馆图书', value: formatNumber(s.total_books || 0), change: '+6.7%', changeType: 'up', icon: 'archive', color: '#10b981' },
    { key: 'borrowed_books', label: '借出量', value: formatNumber(s.cko_count || 0), change: '+10.1%', changeType: 'up', icon: 'arrow-up', color: '#f59e0b' },
    { key: 'returned_books', label: '归还量', value: formatNumber(s.cki_count || 0), change: '+9.3%', changeType: 'up', icon: 'arrow-down', color: '#ef4444' },
    { key: 'library_visits', label: '到馆续借', value: formatNumber(s.reh_count || 0), change: '+6.8%', changeType: 'up', icon: 'refresh', color: '#8b5cf6' },
    { key: 'online_renewals', label: '网上续借', value: formatNumber(s.rei_count || 0), change: '+18.2%', changeType: 'up', icon: 'wifi', color: '#6366f1' }
  ]
})

const categoryColors = ['#818cf8', '#6366f1', '#a78bfa', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#3b82f6', '#8b5cf6', '#ef4444']

const categoryData = computed(() => {
  const cats = props.allData?.books?.categories
  if (!cats || !cats.length) {
    return [
      { name: '文学类', value: 0, percent: 0, color: '#818cf8' },
      { name: '社会科学类', value: 0, percent: 0, color: '#6366f1' },
      { name: '工程技术类', value: 0, percent: 0, color: '#a78bfa' },
      { name: '自然科学类', value: 0, percent: 0, color: '#06b6d4' },
      { name: '人文类', value: 0, percent: 0, color: '#10b981' },
      { name: '宗教类', value: 0, percent: 0, color: '#f59e0b' },
      { name: '综合类', value: 0, percent: 0, color: '#ec4899' }
    ]
  }
  return cats.map((c, i) => ({
    name: c.name,
    value: c.count || 0,
    percent: c.percent || 0,
    color: categoryColors[i % categoryColors.length]
  }))
})

const borrowTypeData = computed(() => {
  const actions = props.allData?.borrows?.actionStats
  if (!actions || !actions.length) {
    return [
      { name: '借出', percent: 38.1, color: '#6366f1' },
      { name: '归还', percent: 26.8, color: '#818cf8' },
      { name: '到馆续借', percent: 13.3, color: '#06b6d4' },
      { name: '网上续借', percent: 7.4, color: '#10b981' }
    ]
  }
  return actions.map((a, i) => ({
    name: a.name || a.action,
    percent: a.percent || 0,
    color: categoryColors[i % categoryColors.length]
  }))
})

const topCategoriesData = computed(() => {
  const cats = props.allData?.books?.categories
  if (!cats || !cats.length) {
    return []
  }
  return cats.slice(0, 10).map((c, i) => ({
    rank: i + 1,
    name: c.name,
    percent: c.percent || 0,
    color: categoryColors[i % categoryColors.length]
  }))
})

const trendData = computed(() => {
  const trend = props.allData?.readers?.monthlyTrend
  if (!trend || !trend.length) {
    return [
      { month: '1月', value: 0 }, { month: '2月', value: 0 }, { month: '3月', value: 0 },
      { month: '4月', value: 0 }, { month: '5月', value: 0 }, { month: '6月', value: 0 },
      { month: '7月', value: 0 }, { month: '8月', value: 0 }, { month: '9月', value: 0 },
      { month: '10月', value: 0 }, { month: '11月', value: 0 }, { month: '12月', value: 0 }
    ]
  }
  return trend.map(t => ({
    month: t.month,
    value: Math.round((t.count || 0) / 1000)
  }))
})

const readerActivityData = computed(() => {
  const types = props.allData?.readers?.readerTypes
  if (!types || !types.length) {
    return [
      { name: '本科', value: 35.1, color: '#06b6d4' },
      { name: '研究生', value: 16.6, color: '#8b5cf6' },
      { name: '大专', value: 15.2, color: '#10b981' },
      { name: '高中', value: 13.0, color: '#f59e0b' },
      { name: '临时', value: 9.4, color: '#ef4444' },
      { name: '小学', value: 5.9, color: '#6366f1' },
      { name: '学龄前', value: 2.6, color: '#3b82f6' },
      { name: '初中', value: 2.3, color: '#818cf8' }
    ]
  }
  const activityColors = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#3b82f6', '#818cf8']
  return types.map((t, i) => ({
    name: t.name,
    value: t.percent || 0,
    color: activityColors[i % activityColors.length]
  }))
})

const todayStats = computed(() => {
  const s = props.allData?.overview?.stats
  return {
    visitors: formatNumber(s?.today_visits || 0) + ' 人',
    borrows: formatNumber(s?.cko_count || 0) + ' 册',
    returns: formatNumber(s?.cki_count || 0) + ' 部'
  }
})

const totalReadersCount = computed(() => {
  const s = props.allData?.overview?.stats
  return formatNumber(s?.total_readers || 0)
})

const totalCategoryBorrows = computed(() => {
  const cats = categoryData.value
  return formatNumber(cats.reduce((sum, c) => sum + (c.value || 0), 0))
})

const hoveredTrendPoint = ref(null)

const onCategoryHover = (name) => {
  highlightedCategory.value = name
}

const onCategoryLeave = () => {
  highlightedCategory.value = null
}

const onBorrowTypeHover = (name) => {
  highlightedBorrowType.value = name
}

const onBorrowTypeLeave = () => {
  highlightedBorrowType.value = null
}

const onReaderActivityHover = (name) => {
  highlightedReaderActivity.value = name
}

const onReaderActivityLeave = () => {
  highlightedReaderActivity.value = null
}

const onCategoryClick = (name) => {
  highlightedCategory.value = highlightedCategory.value === name ? null : name
}

const onTrendPointHover = (idx) => {
  hoveredTrendPoint.value = idx
}

const onTrendPointLeave = () => {
  hoveredTrendPoint.value = null
}

const polarToCartesian = (centerX, centerY, radius, angleInDegrees) => {
  const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0
  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  }
}

const describeArc = (x, y, radius, startAngle, endAngle) => {
  if (endAngle - startAngle >= 360) {
    return [
      'M', x, y - radius,
      'A', radius, radius, 0, 1, 0, x, y + radius,
      'A', radius, radius, 0, 1, 0, x, y - radius,
      'Z'
    ].join(' ')
  }
  const start = polarToCartesian(x, y, radius, endAngle)
  const end = polarToCartesian(x, y, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'
  return ['M', x, y, 'L', start.x, start.y, 'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y, 'Z'].join(' ')
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
  const data = categoryData.value
  for (let i = 0; i < index; i++) sum += data[i]?.percent || 0
  return (sum / 100) * 360
}

const getCategoryEndAngle = (index) => {
  let sum = 0
  const data = categoryData.value
  for (let i = 0; i <= index; i++) sum += data[i]?.percent || 0
  return (sum / 100) * 360
}

const getBorrowTypeStartAngle = (index) => {
  let sum = 0
  const data = borrowTypeData.value
  for (let i = 0; i < index; i++) sum += data[i]?.percent || 0
  return (sum / 100) * 360
}

const getBorrowTypeEndAngle = (index) => {
  let sum = 0
  const data = borrowTypeData.value
  for (let i = 0; i <= index; i++) sum += data[i]?.percent || 0
  return (sum / 100) * 360
}

const getReaderActivityStartAngle = (index) => {
  let sum = 0
  const data = readerActivityData.value
  for (let i = 0; i < index; i++) sum += data[i]?.value || 0
  return (sum / 100) * 360
}

const getReaderActivityEndAngle = (index) => {
  let sum = 0
  const data = readerActivityData.value
  for (let i = 0; i <= index; i++) sum += data[i]?.value || 0
  return (sum / 100) * 360
}

const maxTrendValue = computed(() => {
  const vals = trendData.value.map(d => d.value)
  const max = Math.max(...vals)
  return max === 0 ? 1 : max
})
const minTrendValue = computed(() => Math.min(...trendData.value.map(d => d.value)))

const trendPaths = computed(() => {
  const data = trendData.value
  const width = 800
  const height = 280
  const padding = 40
  const chartWidth = width - padding * 2
  const chartHeight = height - padding * 2
  const maxVal = maxTrendValue.value
  const minVal = minTrendValue.value
  const range = maxVal - minVal || 1

  const points = data.map((d, i) => ({
    x: padding + (i / (data.length - 1 || 1)) * chartWidth,
    y: padding + chartHeight - ((d.value - minVal) / range) * chartHeight
  }))

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  const areaPath = linePath +
    ` L ${points[points.length - 1].x} ${padding + chartHeight}` +
    ` L ${points[0].x} ${padding + chartHeight} Z`

  return { linePath, areaPath, points }
})

const getSliceOpacity = (dataArr, idx, highlightRef) => {
  if (!highlightRef.value) return 1
  return highlightRef.value === dataArr[idx].name ? 1 : 0.35
}

const getBarHighlightClass = (name) => {
  if (!highlightedCategory.value) return ''
  return highlightedCategory.value === name ? 'bar-highlighted' : 'bar-dimmed'
}

const getLegendHighlightClass = (name, type) => {
  const ref = type === 'category' ? highlightedCategory : type === 'borrow' ? highlightedBorrowType : highlightedReaderActivity
  if (!ref.value) return ''
  return ref.value === name ? 'legend-highlighted' : 'legend-dimmed'
}

const getActivitySliceOpacity = (idx) => {
  if (!highlightedReaderActivity.value) return 1
  return highlightedReaderActivity.value === readerActivityData.value[idx].name ? 1 : 0.35
}

const isInitialLoad = ref(true)

const simulateChartLoad = () => {
  const delays = { stats: 80, trend: 150, pie: 200, donut: 250, bar: 300, activity: 350, today: 120 }
  Object.keys(delays).forEach(key => {
    if (isInitialLoad.value) {
      chartLoadingStates[key] = true
    }
    setTimeout(() => {
      chartLoadingStates[key] = false
    }, delays[key])
  })
}

const retryChart = (key) => {
  chartErrorStates[key] = false
  chartLoadingStates[key] = true
  chartRetryCount[key]++
  setTimeout(() => {
    chartLoadingStates[key] = false
  }, 800)
}

watch(() => props.allData, (newVal) => {
  if (newVal) {
    simulateChartLoad()
    nextTick(() => {
      isInitialLoad.value = false
    })
  }
}, { immediate: true, deep: true })
</script>

<template>
  <div class="overview-container">
    <div class="stats-cards-grid">
      <div
        v-for="(card, index) in statsCards"
        :key="card.key"
        class="stat-card"
        :style="{ '--card-color': card.color, '--delay': (index * 0.05) + 's' }"
      >
        <div v-if="chartLoadingStates.stats" class="chart-skeleton skeleton-pulse"></div>
        <template v-else>
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
        </template>
      </div>
    </div>

    <div class="charts-row-primary">
      <div class="chart-card trend-chart-card" :class="{ 'chart-loading': chartLoadingStates.trend }">
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
        <div v-if="chartLoadingStates.trend" class="chart-loading-state">
          <div class="chart-skeleton-chart skeleton-pulse" style="height: 280px"></div>
        </div>
        <div v-else-if="chartErrorStates.trend" class="chart-error-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <span>加载失败</span>
          <button class="retry-btn" @click="retryChart('trend')">重试</button>
        </div>
        <div v-else class="chart-content trend-content">
          <svg viewBox="0 0 800 280" class="trend-svg" preserveAspectRatio="xMidYMid meet">
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
            <path :d="trendPaths.areaPath" fill="url(#areaGradient)" class="trend-area"/>
            <path :d="trendPaths.linePath" fill="none" stroke="#6366f1" stroke-width="3" filter="url(#glow)" stroke-linecap="round" stroke-linejoin="round" class="trend-line"/>
            <g v-for="(point, idx) in trendPaths.points" :key="idx">
              <circle
                :cx="point.x"
                :cy="point.y"
                :r="hoveredTrendPoint === idx ? 7 : 5"
                :fill="hoveredTrendPoint === idx ? '#6366f1' : 'white'"
                :stroke="'#6366f1'"
                :stroke-width="hoveredTrendPoint === idx ? 3 : 2"
                class="data-point"
                @mouseenter="onTrendPointHover(idx)"
                @mouseleave="onTrendPointLeave"
              />
              <text
                v-if="hoveredTrendPoint === idx || idx % 2 === 0"
                :x="point.x"
                :y="point.y - 14"
                text-anchor="middle"
                :font-size="hoveredTrendPoint === idx ? 13 : 10"
                :font-weight="hoveredTrendPoint === idx ? 700 : 400"
                :fill="hoveredTrendPoint === idx ? '#6366f1' : '#94a3b8'"
              >{{ trendData[idx]?.value || 0 }}千</text>
            </g>
            <g v-for="(item, idx) in trendData" :key="'label-' + idx">
              <text :x="40 + (idx / (trendData.length - 1)) * 720" y="270" text-anchor="middle" font-size="11" fill="#94a3b8">{{ item.month }}</text>
            </g>
          </svg>
        </div>
      </div>

      <div class="primary-side-column">
        <div class="chart-card activity-chart-card" :class="{ 'chart-loading': chartLoadingStates.activity }">
          <h3 class="chart-title">读者学历分布</h3>
          <div v-if="chartLoadingStates.activity" class="chart-loading-state">
            <div class="chart-skeleton-chart skeleton-pulse"></div>
          </div>
          <div v-else-if="chartErrorStates.activity" class="chart-error-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <span>加载失败</span>
            <button class="retry-btn" @click="retryChart('activity')">重试</button>
          </div>
          <div v-else class="chart-content activity-content">
            <svg viewBox="0 0 200 200" class="activity-donut-svg">
              <g transform="translate(100, 100)">
                <path
                  v-for="(item, idx) in readerActivityData"
                  :key="idx"
                  :d="describeDonutArc(0, 0, 60, 78, getReaderActivityStartAngle(idx), getReaderActivityEndAngle(idx))"
                  :fill="item.color"
                  class="activity-slice"
                  :class="{ 'slice-dimmed': highlightedReaderActivity && highlightedReaderActivity !== item.name, 'slice-active': highlightedReaderActivity === item.name }"
                  :style="{ opacity: getActivitySliceOpacity(idx) }"
                  @mouseenter="onReaderActivityHover(item.name)"
                  @mouseleave="onReaderActivityLeave"
                />
                <text x="0" y="-5" text-anchor="middle" font-size="22" font-weight="700" fill="#1e293b">{{ totalReadersCount }}</text>
                <text x="0" y="14" text-anchor="middle" font-size="10" fill="#64748b">读者总数</text>
              </g>
            </svg>
            <div class="activity-legend">
              <div
                v-for="(item, idx) in readerActivityData"
                :key="idx"
                class="legend-item-tiny"
                :class="getLegendHighlightClass(item.name, 'reader')"
                @mouseenter="onReaderActivityHover(item.name)"
                @mouseleave="onReaderActivityLeave"
              >
                <span class="legend-dot" :style="{ background: item.color }"></span>
                <span class="legend-name">{{ item.name }}</span>
                <span class="legend-value">{{ item.value }}%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="today-summary-card" :class="{ 'chart-loading': chartLoadingStates.today }">
          <div v-if="chartLoadingStates.today" class="chart-loading-state">
            <div class="chart-skeleton-chart skeleton-pulse" style="height: 120px"></div>
          </div>
          <template v-else>
            <h3 class="today-title">今日概况</h3>
            <div class="today-mini-chart">
              <svg viewBox="0 0 200 80" class="mini-line-chart" preserveAspectRatio="xMidYMid meet">
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
          </template>
        </div>
      </div>
    </div>

    <div class="charts-row-secondary">
      <div class="chart-card pie-chart-card" :class="{ 'chart-loading': chartLoadingStates.pie }">
        <h3 class="chart-title">
          借阅分类分布
          <span v-if="highlightedCategory" class="chart-filter-badge">
            {{ highlightedCategory }}
            <button class="filter-clear" @click="highlightedCategory = null">✕</button>
          </span>
        </h3>
        <div v-if="chartLoadingStates.pie" class="chart-loading-state">
          <div class="chart-skeleton-chart skeleton-pulse"></div>
        </div>
        <div v-else-if="chartErrorStates.pie" class="chart-error-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <span>加载失败</span>
          <button class="retry-btn" @click="retryChart('pie')">重试</button>
        </div>
        <div v-else class="chart-content">
          <svg viewBox="0 0 320 260" class="pie-svg" preserveAspectRatio="xMidYMid meet">
            <g transform="translate(130, 130)">
              <path
                v-for="(item, idx) in categoryData"
                :key="idx"
                :d="describeArc(0, 0, 95, getCategoryStartAngle(idx), getCategoryEndAngle(idx))"
                :fill="item.color"
                stroke="#fff"
                stroke-width="2"
                class="pie-slice"
                :class="{ 'slice-dimmed': highlightedCategory && highlightedCategory !== item.name, 'slice-active': highlightedCategory === item.name }"
                :style="{ opacity: getSliceOpacity(categoryData, idx, highlightedCategory) }"
                @mouseenter="onCategoryHover(item.name)"
                @mouseleave="onCategoryLeave"
                @click="onCategoryClick(item.name)"
              />
              <circle cx="0" cy="0" r="50" fill="white"/>
              <text x="0" y="-8" text-anchor="middle" font-size="22" font-weight="700" fill="#1e293b">{{ totalCategoryBorrows }}</text>
              <text x="0" y="14" text-anchor="middle" font-size="11" fill="#64748b">分类总借阅量</text>
            </g>
          </svg>
          <div class="pie-legend">
            <div
              v-for="(item, idx) in categoryData"
              :key="idx"
              class="legend-item"
              :class="getLegendHighlightClass(item.name, 'category')"
              @mouseenter="onCategoryHover(item.name)"
              @mouseleave="onCategoryLeave"
              @click="onCategoryClick(item.name)"
            >
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-percent">{{ item.percent }}%</span>
              <span class="legend-value">{{ formatNumber(item.value) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-card donut-chart-card" :class="{ 'chart-loading': chartLoadingStates.donut }">
        <h3 class="chart-title">借阅类型占比</h3>
        <div v-if="chartLoadingStates.donut" class="chart-loading-state">
          <div class="chart-skeleton-chart skeleton-pulse"></div>
        </div>
        <div v-else-if="chartErrorStates.donut" class="chart-error-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <span>加载失败</span>
          <button class="retry-btn" @click="retryChart('donut')">重试</button>
        </div>
        <div v-else class="chart-content donut-content">
          <svg viewBox="0 0 220 220" class="donut-svg" preserveAspectRatio="xMidYMid meet">
            <g transform="translate(110, 110)">
              <path
                v-for="(item, idx) in borrowTypeData"
                :key="idx"
                :d="describeDonutArc(0, 0, 65, 90, getBorrowTypeStartAngle(idx), getBorrowTypeEndAngle(idx))"
                :fill="item.color"
                class="donut-slice"
                :class="{ 'slice-dimmed': highlightedBorrowType && highlightedBorrowType !== item.name, 'slice-active': highlightedBorrowType === item.name }"
                :style="{ opacity: getSliceOpacity(borrowTypeData, idx, highlightedBorrowType) }"
                @mouseenter="onBorrowTypeHover(item.name)"
                @mouseleave="onBorrowTypeLeave"
              />
              <text x="0" y="-5" text-anchor="middle" font-size="28" font-weight="700" fill="#1e293b">{{ borrowTypeData[0]?.percent || 0 }}%</text>
              <text x="0" y="16" text-anchor="middle" font-size="12" fill="#64748b">{{ borrowTypeData[0]?.name || '最大占比' }}</text>
            </g>
          </svg>
          <div class="donut-legend">
            <div
              v-for="(item, idx) in borrowTypeData"
              :key="idx"
              class="legend-item-small"
              :class="getLegendHighlightClass(item.name, 'borrow')"
              @mouseenter="onBorrowTypeHover(item.name)"
              @mouseleave="onBorrowTypeLeave"
            >
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-value">{{ item.percent }}%</span>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-card bar-chart-card" :class="{ 'chart-loading': chartLoadingStates.bar }">
        <h3 class="chart-title">
          Top 10 借阅分类占比
          <span v-if="highlightedCategory" class="chart-filter-badge">
            {{ highlightedCategory }}
            <button class="filter-clear" @click="highlightedCategory = null">✕</button>
          </span>
        </h3>
        <div v-if="chartLoadingStates.bar" class="chart-loading-state">
          <div class="chart-skeleton-chart skeleton-pulse"></div>
        </div>
        <div v-else-if="chartErrorStates.bar" class="chart-error-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="error-icon">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <span>加载失败</span>
          <button class="retry-btn" @click="retryChart('bar')">重试</button>
        </div>
        <div v-else class="chart-content bar-content">
          <div
            v-for="(item, idx) in topCategoriesData"
            :key="idx"
            class="bar-item"
            :class="getBarHighlightClass(item.name)"
            @mouseenter="onCategoryHover(item.name)"
            @mouseleave="onCategoryLeave"
            @click="onCategoryClick(item.name)"
          >
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
  </div>
</template>

<style scoped src="./OverviewView.css"></style>
