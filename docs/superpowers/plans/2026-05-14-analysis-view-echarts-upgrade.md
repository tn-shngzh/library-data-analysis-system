# 数据分析板块 ECharts 深度优化 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AnalysisView.vue 三个标签（关联分析、时段对比、热力图）从原生 HTML/CSS 渲染升级为 ECharts 全屏大图表 + 子视图切换，同时后端新增 3 个 API 提供更丰富的图表数据。

**Architecture:** 后端在现有 `/api/analysis` 路由下新增 3 个端点返回趋势/对比数据；前端安装 echarts + vue-echarts 依赖，全局注册 VChart 组件，重写 AnalysisView.vue 使用 ChartCard + ECharts，每个标签内嵌子视图切换器切换图表类型。

**Tech Stack:** Vue 3 + vue-echarts + echarts, FastAPI, PostgreSQL

---

## 文件总览

| 操作 | 文件 |
|------|------|
| 安装 | `package.json` — 添加 echarts + vue-echarts 依赖 |
| 创建 | `src/plugins/echarts.ts` — ECharts 全局注册 |
| 修改 | `src/main.ts` — 注册 echarts 插件 |
| 新增 | `src/components/ChartViewSwitcher.vue` — 子视图切换器组件 |
| 重写 | `src/views/AnalysisView.vue` — 核心改造 |
| 修改 | `src/api/analysis.ts` — 新增 3 个 API 调用 |
| 修改 | `src/i18n/locales/zh-CN/analysis.ts` — 新增 i18n key |
| 修改 | `src/i18n/locales/en/analysis.ts` — 英文翻译 |
| 修改 | `src/i18n/locales/zh-TW/analysis.ts` — 繁体翻译 |
| 修改 | `src/i18n/locales/ja/analysis.ts` — 日文翻译 |
| 修改 | `library_data_analysis_fastapi/app/routers/analysis.py` — 新增 3 个 API 端点 |

---

### Task 1: 安装 ECharts 依赖

**Files:**
- Modify: `library_data_analysis_vue/package.json`

- [ ] **Step 1: 安装 echarts 和 vue-echarts**

```bash
cd library_data_analysis_vue && npm install echarts vue-echarts
```

- [ ] **Step 2: 验证安装**

```bash
cd library_data_analysis_vue && npm ls echarts vue-echarts
```

Expected: 显示 echarts 和 vue-echarts 版本号，无错误。

---

### Task 2: 全局注册 ECharts 组件

**Files:**
- Create: `library_data_analysis_vue/src/plugins/echarts.ts`
- Modify: `library_data_analysis_vue/src/main.ts`

- [ ] **Step 1: 创建 echarts 插件文件**

```typescript
// src/plugins/echarts.ts
import { use } from "echarts/core"
import { CanvasRenderer } from "echarts/renderers"
import {
  BarChart,
  LineChart,
  PieChart,
  HeatmapChart,
  RadarChart,
  ScatterChart
} from "echarts/charts"
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  MarkLineComponent,
  MarkPointComponent,
  GraphicComponent
} from "echarts/components"
import VChart from "vue-echarts"

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  HeatmapChart,
  RadarChart,
  ScatterChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  ToolboxComponent,
  DataZoomComponent,
  VisualMapComponent,
  MarkLineComponent,
  MarkPointComponent,
  GraphicComponent
])

export { VChart }
```

- [ ] **Step 2: 在 main.ts 中注册**

在 `main.ts` 的 `import i18n from './i18n'` 之后、`const app = createApp(App)` 之后添加：

```typescript
import { VChart } from './plugins/echarts'
// ... existing code ...
const app = createApp(App)
app.component('v-chart', VChart)
```

完整 main.ts：

```typescript
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { VChart } from './plugins/echarts'

const app = createApp(App)

app.component('v-chart', VChart)
app.use(createPinia())
app.use(router)
app.use(i18n)

app.mount('#app')
```

- [ ] **Step 3: 验证构建**

```bash
cd library_data_analysis_vue && npm run build
```

Expected: 构建成功，无错误。

---

### Task 3: 创建 ChartViewSwitcher 子视图切换器组件

**Files:**
- Create: `library_data_analysis_vue/src/components/ChartViewSwitcher.vue`

- [ ] **Step 1: 创建组件文件**

```vue
<script setup>
defineProps({
  views: {
    type: Array,
    required: true
  },
  modelValue: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="view-switcher">
    <button
      v-for="view in views"
      :key="view.key"
      class="switch-btn"
      :class="{ active: modelValue === view.key }"
      @click="emit('update:modelValue', view.key)"
    >
      <svg v-if="view.icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="switch-icon" v-html="view.icon" />
      {{ view.label }}
    </button>
  </div>
</template>

<style scoped>
.view-switcher {
  display: flex;
  gap: 2px;
  background: var(--color-neutral-100);
  border-radius: 8px;
  padding: 3px;
}

.switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-neutral-500);
  transition: all 0.2s;
  white-space: nowrap;
}

.switch-btn:hover {
  color: var(--color-neutral-700);
}

.switch-btn.active {
  background: white;
  color: var(--color-primary-600);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.switch-icon {
  width: 15px;
  height: 15px;
}
</style>
```

- [ ] **Step 2: 验证构建**

```bash
cd library_data_analysis_vue && npm run build
```

Expected: 构建成功。

---

### Task 4: 新增后端 API — 学历月度趋势

**Files:**
- Modify: `library_data_analysis_fastapi/app/routers/analysis.py`

- [ ] **Step 1: 在 analysis.py 末尾添加新端点**

在文件末尾（第 205 行 `raise HTTPException(...)` 之后）添加：

```python
@router.get("/degree-monthly-trend")
async def get_degree_monthly_trend(year: Optional[int] = None, current_user=Depends(get_current_user)):
    cache_key = f"analysis:degree_trend:{year}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            nonlocal year
            with conn.cursor() as cur:
                today = datetime.now().date()
                if year is None:
                    cur.execute("SELECT MAX(borrow_date) FROM circulations WHERE status = 'borrowed'")
                    row = cur.fetchone()
                    year = (row[0] // 10000) if row and row[0] else today.year

                if year != today.year:
                    start = int(f"{year}0101")
                    end = int(f"{year}1231")
                else:
                    start = int(f"{today.year}0101")
                    end = int(today.strftime('%Y%m%d'))

                cur.execute("""
                    SELECT b.degree,
                           MOD(c.borrow_date, 10000) / 100 as month,
                           COUNT(*) as count
                    FROM circulations c
                    JOIN borrowers b ON c.borrower_id = b.id
                    WHERE c.borrow_date BETWEEN %s AND %s
                    GROUP BY b.degree, month
                    ORDER BY b.degree, month
                """, (start, end))
                rows = cur.fetchall()

                degrees_order = list(education_levels.keys())
                month_set = set()
                data_map = {}
                for row in rows:
                    deg, month, count = row
                    month_set.add(int(month))
                    data_map[(deg, int(month))] = count

                months_list = sorted(month_set)
                month_names = [f"{m}月" for m in months_list]

                series = []
                for deg in degrees_order:
                    if deg not in set(r[0] for r in rows):
                        continue
                    deg_data = []
                    for m in months_list:
                        deg_data.append(data_map.get((deg, m), 0))
                    deg_name = education_levels.get(deg, deg)
                    series.append({
                        "name": deg_name,
                        "data": deg_data
                    })

                return {"months": month_names, "series": series}

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 3600)
        return result
    except Exception as e:
        logger.error("获取学历月度趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取学历月度趋势失败: {e}")
```

- [ ] **Step 2: 重启后端验证**

```bash
# 检查语法
cd library_data_analysis_fastapi && python -c "from app.routers.analysis import router; print('OK')"
```

Expected: 输出 "OK"，无 ImportError 或 SyntaxError。

---

### Task 5: 新增后端 API — 按日明细趋势

**Files:**
- Modify: `library_data_analysis_fastapi/app/routers/analysis.py`

- [ ] **Step 1: 在上一个端点后继续添加**

```python
@router.get("/daily-trend")
async def get_daily_trend(
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    today = datetime.now().date()
    if start_date is None:
        start_date = int(today.replace(day=1).strftime('%Y%m%d'))
    if end_date is None:
        end_date = int(today.strftime('%Y%m%d'))

    cache_key = f"analysis:daily:{start_date}:{end_date}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT borrow_date,
                           COUNT(*) as total,
                           COUNT(CASE WHEN status = 'borrowed' THEN 1 END) as borrowed,
                           COUNT(CASE WHEN status = 'returned' THEN 1 END) as returned
                    FROM circulations
                    WHERE borrow_date BETWEEN %s AND %s
                    GROUP BY borrow_date
                    ORDER BY borrow_date
                """, (start_date, end_date))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()

                dates = []
                total_series = []
                borrowed_series = []
                returned_series = []

                for row in rows:
                    d = dict(zip(columns, row))
                    date_str = str(d['borrow_date'])
                    dates.append(f"{date_str[4:6]}/{date_str[6:8]}")
                    total_series.append(d['total'])
                    borrowed_series.append(d['borrowed'])
                    returned_series.append(d['returned'])

                return {
                    "dates": dates,
                    "total": total_series,
                    "borrowed": borrowed_series,
                    "returned": returned_series
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取每日趋势失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取每日趋势失败: {e}")
```

- [ ] **Step 2: 语法验证**

```bash
cd library_data_analysis_fastapi && python -c "from app.routers.analysis import router; print('OK')"
```

---

### Task 6: 新增后端 API — 分类级别时段对比

**Files:**
- Modify: `library_data_analysis_fastapi/app/routers/analysis.py`

- [ ] **Step 1: 继续添加端点**

```python
@router.get("/category-period-comparison")
async def get_category_period_comparison(
    period1_start: Optional[int] = None,
    period1_end: Optional[int] = None,
    period2_start: Optional[int] = None,
    period2_end: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    today = datetime.now().date()
    if period1_start is None:
        period1_start = int(today.replace(day=1).strftime('%Y%m%d'))
    if period1_end is None:
        period1_end = int(today.strftime('%Y%m%d'))
    if period2_start is None:
        last_month = today.replace(day=1) - timedelta(days=1)
        period2_start = int(last_month.replace(day=1).strftime('%Y%m%d'))
    if period2_end is None:
        last_month = today.replace(day=1) - timedelta(days=1)
        period2_end = int(last_month.strftime('%Y%m%d'))

    cache_key = f"analysis:cat_period:{period1_start}:{period1_end}:{period2_start}:{period2_end}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        def _query(conn):
            with conn.cursor() as cur:
                def get_cat_stats(s, e):
                    cur.execute("""
                        SELECT bc.category, COUNT(*) as count
                        FROM circulations c
                        JOIN book_categories bc ON c.bib_id = bc.bib_id
                        WHERE c.borrow_date BETWEEN %s AND %s
                        GROUP BY bc.category
                        ORDER BY count DESC
                    """, (s, e))
                    return {row[0]: row[1] for row in cur.fetchall()}

                p1 = get_cat_stats(period1_start, period1_end)
                p2 = get_cat_stats(period2_start, period2_end)

                all_cats = set(list(p1.keys()) + list(p2.keys()))
                comparison = []
                for cat in all_cats:
                    v1 = p1.get(cat, 0)
                    v2 = p2.get(cat, 0)
                    if v2 > 0:
                        change = round((v1 - v2) / v2 * 100, 1)
                    elif v1 > 0:
                        change = 100.0
                    else:
                        change = 0.0
                    comparison.append({
                        "category": cat,
                        "period1_count": v1,
                        "period2_count": v2,
                        "change": change
                    })

                comparison.sort(key=lambda x: x['change'], reverse=True)

                return {
                    "period1_start": period1_start,
                    "period1_end": period1_end,
                    "period2_start": period2_start,
                    "period2_end": period2_end,
                    "comparison": comparison
                }

        result = await run_sync_db(_query)
        cache.cache_set(cache_key, result, 600)
        return result
    except Exception as e:
        logger.error("获取分类时段对比失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取分类时段对比失败: {e}")
```

- [ ] **Step 2: 语法验证**

```bash
cd library_data_analysis_fastapi && python -c "from app.routers.analysis import router; print('OK')"
```

---

### Task 7: 新增前端 API 调用

**Files:**
- Modify: `library_data_analysis_vue/src/api/analysis.ts`

- [ ] **Step 1: 在 analysis.ts 的 analysisApi 对象中新增 3 个方法**

```typescript
import { get } from './index'

export const analysisApi = {
  getCorrelation: (year?: number) => {
    const params = year ? `?year=${year}` : ''
    return get(`/api/analysis/correlation${params}`)
  },
  getPeriodComparison: (p1Start?: number, p1End?: number, p2Start?: number, p2End?: number) => {
    const params = new URLSearchParams()
    if (p1Start) params.append('period1_start', p1Start.toString())
    if (p1End) params.append('period1_end', p1End.toString())
    if (p2Start) params.append('period2_start', p2Start.toString())
    if (p2End) params.append('period2_end', p2End.toString())
    const qs = params.toString()
    return get(`/api/analysis/period-comparison${qs ? '?' + qs : ''}`)
  },
  getCategoryHeatmap: (year?: number, months?: number) => {
    const params = new URLSearchParams()
    if (year) params.append('year', year.toString())
    if (months) params.append('months', months.toString())
    const qs = params.toString()
    return get(`/api/analysis/category-heatmap${qs ? '?' + qs : ''}`)
  },
  getDegreeMonthlyTrend: (year?: number) => {
    const params = year ? `?year=${year}` : ''
    return get(`/api/analysis/degree-monthly-trend${params}`)
  },
  getDailyTrend: (startDate?: number, endDate?: number) => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate.toString())
    if (endDate) params.append('end_date', endDate.toString())
    const qs = params.toString()
    return get(`/api/analysis/daily-trend${qs ? '?' + qs : ''}`)
  },
  getCategoryPeriodComparison: (p1Start?: number, p1End?: number, p2Start?: number, p2End?: number) => {
    const params = new URLSearchParams()
    if (p1Start) params.append('period1_start', p1Start.toString())
    if (p1End) params.append('period1_end', p1End.toString())
    if (p2Start) params.append('period2_start', p2Start.toString())
    if (p2End) params.append('period2_end', p2End.toString())
    const qs = params.toString()
    return get(`/api/analysis/category-period-comparison${qs ? '?' + qs : ''}`)
  }
}
```

---

### Task 8: 新增 i18n 翻译 key

**Files:**
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-CN/analysis.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/en/analysis.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-TW/analysis.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/ja/analysis.ts`

- [ ] **Step 1: 更新中文 (zh-CN)**

```typescript
export default {
  title: '数据分析',
  desc: '跨维度关联分析与对比',
  correlation: '关联分析',
  comparison: '时段对比',
  heatmap: '分类热力图',
  readerTypeBorrow: '读者类型借阅关联',
  degree: '学历类型',
  totalBorrow: '总借阅',
  checkout: '借出',
  checkin: '归还',
  renewal: '馆内续借',
  onlineRenewal: '线上续借',
  avgPerReader: '人均借阅',
  actionDistribution: '操作类型分布',
  periodSettings: '时段设置',
  period1: '时段一',
  period2: '时段二',
  startPlaceholder: '起始日期(YYYYMMDD)',
  endPlaceholder: '结束日期(YYYYMMDD)',
  compare: '对比分析',
  totalCirculation: '总流通量',
  activeReaders: '活跃读者',
  categoryHeatmap: '分类借阅热力图',
  category: '分类',
  low: '低',
  high: '高',
  viewBar: '柱状图',
  viewPie: '饼图',
  viewRadar: '雷达图',
  viewLine: '折线图',
  viewStacked: '堆积柱状图',
  viewHeatmap: '热力图',
  viewRanking: '涨跌排行',
  degreeMonthlyTrend: '各学历月度借阅趋势',
  dailyTrend: '按日趋势对比',
  categoryComparison: '分类涨跌对比',
  trendOverview: '趋势总览',
  categoryChangeRanking: '分类涨跌排行',
  period1Label: '时段一',
  period2Label: '时段二',
  changeRate: '变化率',
  total: '总计'
}
```

- [ ] **Step 2: 更新英文 (en)**

读出 `en/analysis.ts` 并换成英文翻译。

- [ ] **Step 3: 更新繁体 (zh-TW)**

读出 `zh-TW/analysis.ts` 并换成繁体翻译。

- [ ] **Step 4: 更新日文 (ja)**

读出 `ja/analysis.ts` 并换成日文翻译。

---

### Task 9: 重写 AnalysisView.vue — 关联分析标签

**Files:**
- Rewrite: `library_data_analysis_vue/src/views/AnalysisView.vue`

- [ ] **Step 1: 完整 rewrite AnalysisView.vue**

用 ECharts 全屏图表 + ChartCard + ChartViewSwitcher 模式完全重写。

完整代码如下：

```vue
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { analysisApi } from '@/api/analysis'
import { formatNumber } from '@/utils/format'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'
import ChartViewSwitcher from '@/components/ChartViewSwitcher.vue'

const { t } = useI18n()

const loading = ref(false)
const activeTab = ref('correlation')
const correlationSubView = ref('bar')
const comparisonSubView = ref('bar')
const heatmapSubView = ref('heatmap')

const correlationData = ref({ reader_type_borrow: [], action_distribution: [] })
const degreeTrendData = ref({ months: [], series: [] })
const comparisonData = ref({ period1: {}, period2: {}, changes: {} })
const dailyTrendData = ref({ dates: [], total: [], borrowed: [], returned: [] })
const catComparisonData = ref({ comparison: [] })
const heatmapData = ref({ categories: [], months: [], values: [] })

const period1Start = ref('')
const period1End = ref('')
const period2Start = ref('')
const period2End = ref('')

const tabs = [
  { id: 'correlation', i18nKey: 'analysis.correlation' },
  { id: 'comparison', i18nKey: 'analysis.comparison' },
  { id: 'heatmap', i18nKey: 'analysis.heatmap' }
]

const correlationViews = [
  { key: 'bar', label: t('analysis.viewBar'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { key: 'line', label: t('analysis.viewLine'), icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' },
  { key: 'pie', label: t('analysis.viewPie'), icon: '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>' },
  { key: 'radar', label: t('analysis.viewRadar'), icon: '<polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="8.5" x2="22" y2="8.5"/>' }
]

const comparisonViews = [
  { key: 'bar', label: t('analysis.viewBar'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { key: 'line', label: t('analysis.viewLine'), icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' },
  { key: 'ranking', label: t('analysis.viewRanking'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' }
]

const heatmapViews = [
  { key: 'heatmap', label: t('analysis.viewHeatmap'), icon: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>' },
  { key: 'stacked', label: t('analysis.viewStacked'), icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>' },
  { key: 'line', label: t('analysis.viewLine'), icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' }
]

const fetchAll = async () => {
  loading.value = true
  try {
    await Promise.all([fetchCorrelation(), fetchDegreeTrend(), fetchComparison(), fetchDailyTrend(), fetchCatComparison(), fetchHeatmap()])
  } finally {
    loading.value = false
  }
}

const fetchCorrelation = async () => {
  try {
    const data = await analysisApi.getCorrelation()
    if (data) correlationData.value = data
  } catch (e) { console.error('Failed to fetch correlation data', e) }
}

const fetchDegreeTrend = async () => {
  try {
    const data = await analysisApi.getDegreeMonthlyTrend()
    if (data) degreeTrendData.value = data
  } catch (e) { console.error('Failed to fetch degree trend', e) }
}

const fetchComparison = async () => {
  try {
    const data = await analysisApi.getPeriodComparison(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined,
      period2Start.value ? parseInt(period2Start.value) : undefined,
      period2End.value ? parseInt(period2End.value) : undefined
    )
    if (data) comparisonData.value = data
  } catch (e) { console.error('Failed to fetch comparison data', e) }
}

const fetchDailyTrend = async () => {
  try {
    const data = await analysisApi.getDailyTrend(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined
    )
    if (data) dailyTrendData.value = data
  } catch (e) { console.error('Failed to fetch daily trend', e) }
}

const fetchCatComparison = async () => {
  try {
    const data = await analysisApi.getCategoryPeriodComparison(
      period1Start.value ? parseInt(period1Start.value) : undefined,
      period1End.value ? parseInt(period1End.value) : undefined,
      period2Start.value ? parseInt(period2Start.value) : undefined,
      period2End.value ? parseInt(period2End.value) : undefined
    )
    if (data) catComparisonData.value = data
  } catch (e) { console.error('Failed to fetch cat comparison', e) }
}

const fetchHeatmap = async () => {
  try {
    const data = await analysisApi.getCategoryHeatmap()
    if (data) heatmapData.value = data
  } catch (e) { console.error('Failed to fetch heatmap data', e) }
}

const refreshTabData = () => {
  if (activeTab.value === 'correlation') {
    fetchCorrelation()
    fetchDegreeTrend()
  } else if (activeTab.value === 'comparison') {
    fetchComparison()
    fetchDailyTrend()
    fetchCatComparison()
  } else {
    fetchHeatmap()
  }
}

const CHART_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

const barOption = computed(() => {
  const data = correlationData.value.reader_type_borrow || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['借出', '归还'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.degree_name), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '借阅量' },
    series: [
      { name: '借出', type: 'bar', data: data.map(d => d.borrowed || 0), itemStyle: { color: '#5470c6', borderRadius: [4, 4, 0, 0] }, barGap: '20%' },
      { name: '归还', type: 'bar', data: data.map(d => d.returned || 0), itemStyle: { color: '#91cc75', borderRadius: [4, 4, 0, 0] } }
    ]
  }
})

const lineOption = computed(() => {
  const months = degreeTrendData.value.months || []
  const series = (degreeTrendData.value.series || []).map((s, i) => ({
    name: s.name,
    type: 'line',
    data: s.data,
    smooth: true,
    lineStyle: { width: 3 },
    itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    symbol: 'circle',
    symbolSize: 6
  }))
  return {
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', bottom: 0, data: series.map(s => s.name) },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: months, boundaryGap: false },
    yAxis: { type: 'value', name: '借阅量' },
    series
  }
})

const pieOption = computed(() => {
  const data = (correlationData.value.action_distribution || []).map(d => ({
    name: d.name,
    value: d.count
  }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: false,
      label: { show: true, formatter: '{b}\n{d}%' },
      emphasis: { label: { fontSize: 18, fontWeight: 'bold' } },
      data,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 }
    }]
  }
})

const radarOption = computed(() => {
  const data = correlationData.value.reader_type_borrow || []
  const indicators = [
    { name: '借出', max: Math.max(...data.map(d => d.borrowed || 0), 1) * 1.2 },
    { name: '归还', max: Math.max(...data.map(d => d.returned || 0), 1) * 1.2 },
    { name: '人均借阅', max: Math.max(...data.map(d => d.avg_per_reader || 0), 1) * 1.2 },
    { name: '活跃读者', max: Math.max(...data.map(d => d.reader_count || 0), 1) * 1.2 }
  ]
  const seriesData = data.map((d, i) => ({
    name: d.degree_name,
    value: [d.borrowed || 0, d.returned || 0, d.avg_per_reader || 0, d.reader_count || 0],
    lineStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    areaStyle: { color: CHART_COLORS[i % CHART_COLORS.length], opacity: 0.1 }
  }))
  return {
    tooltip: {},
    legend: { bottom: 0, data: data.map(d => d.degree_name) },
    radar: { indicator: indicators, center: ['50%', '48%'], radius: '62%' },
    series: [{ type: 'radar', data: seriesData }]
  }
})

const comparisonBarOption = computed(() => {
  const p1 = comparisonData.value.period1 || {}
  const p2 = comparisonData.value.period2 || {}
  const labels = ['总流通量', '借出量', '归还量', '活跃读者']
  const keys = ['total', 'borrowed', 'returned', 'active_readers']
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: [t('analysis.period1'), t('analysis.period2')], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', name: '数量' },
    series: [
      { name: t('analysis.period1'), type: 'bar', data: keys.map(k => p1[k] || 0), itemStyle: { color: '#5470c6', borderRadius: [4, 4, 0, 0] }, barGap: '20%' },
      { name: t('analysis.period2'), type: 'bar', data: keys.map(k => p2[k] || 0), itemStyle: { color: '#91cc75', borderRadius: [4, 4, 0, 0] } }
    ]
  }
})

const comparisonLineOption = computed(() => {
  const dates = dailyTrendData.value.dates || []
  const total = dailyTrendData.value.total || []
  const borrowed = dailyTrendData.value.borrowed || []
  const returned = dailyTrendData.value.returned || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, data: ['总流通', '借出', '归还'] },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: { type: 'value', name: '数量' },
    series: [
      { name: '总流通', type: 'line', data: total, smooth: true, lineStyle: { width: 3, color: '#5470c6' }, symbol: 'circle', symbolSize: 4 },
      { name: '借出', type: 'line', data: borrowed, smooth: true, lineStyle: { width: 2, color: '#91cc75' }, symbol: 'circle', symbolSize: 3 },
      { name: '归还', type: 'line', data: returned, smooth: true, lineStyle: { width: 2, color: '#fac858' }, symbol: 'circle', symbolSize: 3 }
    ]
  }
})

const comparisonRankingOption = computed(() => {
  const items = (catComparisonData.value.comparison || []).slice(0, 12)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0]
        const item = items[p.dataIndex]
        if (!item) return ''
        return `${item.category}<br/>时段一: ${item.period1_count}<br/>时段二: ${item.period2_count}<br/>变化: ${item.change >= 0 ? '+' : ''}${item.change}%`
      }
    },
    grid: { left: '3%', right: '8%', bottom: '8%', top: '6%', containLabel: true },
    xAxis: { type: 'value', name: '变化率(%)' },
    yAxis: {
      type: 'category',
      data: items.map(d => d.category).reverse(),
      axisLabel: { fontSize: 12 }
    },
    series: [{
      type: 'bar',
      data: items.map(d => d.change).reverse(),
      itemStyle: {
        color: (params) => {
          const val = items.toReversed()[params.dataIndex]?.change || 0
          return val >= 0 ? '#91cc75' : '#ee6666'
        },
        borderRadius: [0, 4, 4, 0]
      },
      label: { show: true, position: 'right', formatter: '{c}%', fontSize: 12 }
    }]
  }
})

const heatmapOption = computed(() => {
  const categories = heatmapData.value.categories || []
  const months = heatmapData.value.months || []
  const values = heatmapData.value.values || []
  const data = []
  let maxVal = 1
  categories.forEach((cat, ci) => {
    (values[ci] || []).forEach((val, mi) => {
      data.push([mi, ci, val])
      if (val > maxVal) maxVal = val
    })
  })
  return {
    tooltip: {
      position: 'top',
      formatter: (p) => `${categories[p.value[1]]} - ${months[p.value[0]]}<br/>借阅量: ${p.value[2]}`
    },
    grid: { left: '12%', right: '5%', bottom: '8%', top: '6%' },
    xAxis: { type: 'category', data: months, splitArea: { show: true } },
    yAxis: { type: 'category', data: categories, splitArea: { show: true } },
    visualMap: {
      min: 0,
      max: maxVal,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#f0f9ff', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#0284c7'] }
    },
    series: [{
      type: 'heatmap',
      data,
      label: { show: true, fontSize: 10 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } }
    }]
  }
})

const stackedBarOption = computed(() => {
  const categories = heatmapData.value.categories || []
  const months = heatmapData.value.months || []
  const values = heatmapData.value.values || []
  const series = categories.map((cat, ci) => ({
    name: cat,
    type: 'bar',
    data: values[ci] || [],
    stack: 'total',
    emphasis: { focus: 'series' }
  }))
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { type: 'scroll', bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '6%', containLabel: true },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', name: '借阅量' },
    series
  }
})

const heatmapLineOption = computed(() => {
  const categories = heatmapData.value.categories || []
  const months = heatmapData.value.months || []
  const values = heatmapData.value.values || []
  const series = categories.map((cat, ci) => ({
    name: cat,
    type: 'line',
    data: values[ci] || [],
    smooth: true,
    symbol: 'circle',
    symbolSize: 5
  }))
  return {
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '14%', top: '6%', containLabel: true },
    xAxis: { type: 'category', data: months, boundaryGap: false },
    yAxis: { type: 'value', name: '借阅量' },
    series
  }
})

const switchTab = (tabId) => {
  activeTab.value = tabId
  refreshTabData()
}

const comparePeriods = () => {
  fetchComparison()
  fetchDailyTrend()
  fetchCatComparison()
}

onMounted(() => {
  fetchAll()
})
</script>

<template>
  <div class="analysis-view">
    <PageHeader
      :title="t('analysis.title')"
      :description="t('analysis.desc')"
      :loading="loading"
      @refresh="refreshTabData"
    />

    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="switchTab(tab.id)"
      >
        {{ t(tab.i18nKey) }}
      </button>
    </div>

    <LoadingSpinner :loading="loading">
      <!-- 关联分析 -->
      <div v-if="activeTab === 'correlation'" class="tab-content">
        <ChartCard :title="t('analysis.readerTypeBorrow')" color="#5470c6">
          <template #actions>
            <ChartViewSwitcher v-model="correlationSubView" :views="correlationViews" />
          </template>
          <div class="chart-stage">
            <v-chart v-if="correlationSubView === 'bar'" class="full-chart" :option="barOption" autoresize />
            <v-chart v-else-if="correlationSubView === 'line'" class="full-chart" :option="lineOption" autoresize />
            <v-chart v-else-if="correlationSubView === 'pie'" class="full-chart" :option="pieOption" autoresize />
            <v-chart v-else-if="correlationSubView === 'radar'" class="full-chart" :option="radarOption" autoresize />
          </div>
        </ChartCard>
      </div>

      <!-- 时段对比 -->
      <div v-if="activeTab === 'comparison'" class="tab-content">
        <div class="period-controls">
          <div class="period-group">
            <label>{{ t('analysis.period1') }}</label>
            <div class="input-row">
              <input v-model="period1Start" type="number" :placeholder="t('analysis.startPlaceholder')" class="period-input" />
              <span class="input-sep">-</span>
              <input v-model="period1End" type="number" :placeholder="t('analysis.endPlaceholder')" class="period-input" />
            </div>
          </div>
          <div class="period-group">
            <label>{{ t('analysis.period2') }}</label>
            <div class="input-row">
              <input v-model="period2Start" type="number" :placeholder="t('analysis.startPlaceholder')" class="period-input" />
              <input v-model="period2End" type="number" :placeholder="t('analysis.endPlaceholder')" class="period-input" />
            </div>
          </div>
          <button class="compare-btn" @click="comparePeriods">{{ t('analysis.compare') }}</button>
        </div>

        <ChartCard :title="t('analysis.periodComparison')" color="#3ba272">
          <template #actions>
            <ChartViewSwitcher v-model="comparisonSubView" :views="comparisonViews" />
          </template>
          <div class="chart-stage">
            <v-chart v-if="comparisonSubView === 'bar'" class="full-chart" :option="comparisonBarOption" autoresize />
            <v-chart v-else-if="comparisonSubView === 'line'" class="full-chart" :option="comparisonLineOption" autoresize />
            <v-chart v-else-if="comparisonSubView === 'ranking'" class="full-chart" :option="comparisonRankingOption" autoresize />
          </div>
        </ChartCard>
      </div>

      <!-- 热力图 -->
      <div v-if="activeTab === 'heatmap'" class="tab-content">
        <ChartCard :title="t('analysis.categoryHeatmap')" color="#0ea5e9">
          <template #actions>
            <ChartViewSwitcher v-model="heatmapSubView" :views="heatmapViews" />
          </template>
          <div class="chart-stage">
            <v-chart v-if="heatmapSubView === 'heatmap'" class="full-chart heatmap-chart" :option="heatmapOption" autoresize />
            <v-chart v-else-if="heatmapSubView === 'stacked'" class="full-chart" :option="stackedBarOption" autoresize />
            <v-chart v-else-if="heatmapSubView === 'line'" class="full-chart" :option="heatmapLineOption" autoresize />
          </div>
        </ChartCard>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.analysis-view {
  padding: 0;
}

.tab-nav {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: var(--color-neutral-100);
  border-radius: 10px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-neutral-500);
  transition: all 0.2s;
}

.tab-btn.active {
  background: white;
  color: var(--color-neutral-900);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.tab-btn:hover:not(.active) {
  color: var(--color-neutral-700);
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-stage {
  width: 100%;
  min-height: 480px;
}

.full-chart {
  width: 100%;
  height: 480px;
}

.heatmap-chart {
  height: 560px;
}

.period-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  padding: 16px;
  background: var(--color-bg-primary, #fff);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  margin-bottom: 8px;
}

.period-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.period-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-neutral-500);
}

.input-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.period-input {
  padding: 8px 12px;
  border: 1px solid var(--color-neutral-200);
  border-radius: 8px;
  font-size: 14px;
  width: 130px;
  background: var(--color-bg-primary, #fff);
  color: var(--color-neutral-900);
}

.period-input:focus {
  outline: none;
  border-color: #5470c6;
  box-shadow: 0 0 0 3px rgba(84, 112, 198, 0.1);
}

.input-sep {
  color: var(--color-neutral-400);
}

.compare-btn {
  padding: 8px 20px;
  background: #5470c6;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.compare-btn:hover {
  background: #4161b0;
}
</style>
```

- [ ] **Step 2: 验证构建**

```bash
cd library_data_analysis_vue && npm run build
```

Expected: 构建成功，无错误。

---

### Task 10: 全链路验证

**Files:** 以上所有修改。

- [ ] **Step 1: 启动后端并验证 API**

```bash
cd library_data_analysis_fastapi && python -c "import uvicorn; uvicorn.run or check"
```

直接检查新增端点是否可访问（需要先启动后端，然后 curl 测试）。

- [ ] **Step 2: 前端构建最终验证**

```bash
cd library_data_analysis_vue && npm run build
```

Expected: `✓ built in Xs`，无错误。

---

**计划完成。** 总结构为：
- **Task 1-2**：安装依赖 + 全局注册 ECharts
- **Task 3**：创建子视图切换器组件
- **Task 4-6**：后端新增 3 个 API（学历月度趋势 / 按日趋势 / 分类时段对比）
- **Task 7**：前端 API 层新增调用
- **Task 8**：i18n 翻译补全
- **Task 9**：重写 AnalysisView.vue，全屏 ECharts + 子视图切换
- **Task 10**：全链路验证