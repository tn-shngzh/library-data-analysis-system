# 统计分析页面升级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全面升级统计分析页面，修复BUG、优化交互体验、增加筛选功能、添加快照导出功能

**Architecture:** 保持现有5个Tab结构不变，每个Tab增加概览卡片和筛选控件；后端修复BUG并添加book_categories索引；新增快照API存储临时快照供导出页面使用

**Tech Stack:** Vue 3 + TypeScript, ECharts, FastAPI, PostgreSQL, i18n (4语言)

---

## File Structure

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| Modify | `library_data_analysis_vue/src/views/StatisticsView.vue` | 页面主组件：增加概览卡片、筛选控件、快照按钮、错误/空状态 |
| Modify | `library_data_analysis_vue/src/views/StatisticsView.css` | 样式：signal-card风格、筛选控件、快照按钮样式 |
| Modify | `library_data_analysis_vue/src/api/statistics.ts` | API层：添加saveSnapshot方法 |
| Modify | `library_data_analysis_fastapi/app/routers/statistics.py` | 后端：修复forecast截断BUG、实现period参数、添加快照端点 |
| Modify | `library_data_analysis_fastapi/app/database.py` | 添加book_categories(bib_id)索引 |
| Modify | `library_data_analysis_vue/src/api/index.ts` | SWR缓存配置：添加stats路径缓存策略 |
| Modify | `library_data_analysis_vue/src/i18n/locales/zh-CN/stats.ts` | 中文i18n：新增key |
| Modify | `library_data_analysis_vue/src/i18n/locales/en/stats.ts` | 英文i18n |
| Modify | `library_data_analysis_vue/src/i18n/locales/zh-TW/stats.ts` | 繁体i18n |
| Modify | `library_data_analysis_vue/src/i18n/locales/ja/stats.ts` | 日文i18n |

---

### Task 1: 修复后端BUG + 添加索引

**Files:**
- Modify: `library_data_analysis_fastapi/app/routers/statistics.py`
- Modify: `library_data_analysis_fastapi/app/database.py`

- [ ] **Step 1: 修复forecast截断BUG**

在 `statistics.py` 的 regression/forecast 端点中，找到 `forecast[:7]` 改为 `forecast[:forecast_days]`：

```python
# 旧代码 (约第595行)
forecast[:7]

# 新代码
forecast[:forecast_days]
```

- [ ] **Step 2: 实现descriptive端点的period参数**

修改 descriptive 端点的SQL查询，根据 `period` 参数（daily/monthly/weekly）调整GROUP BY粒度：

```python
# 在 _query 函数中，根据 period 参数选择不同的SQL
if period == 'monthly':
    date_expr = "(borrow_date / 100) as period_key"
elif period == 'weekly':
    date_expr = "((borrow_date - 20200101) / 7) as period_key"
else:  # daily
    date_expr = "borrow_date as period_key"

# SQL模板
cur.execute(f"""
    SELECT {date_expr}, COUNT(*) as count
    FROM circulations
    WHERE borrow_date BETWEEN %s AND %s AND status = 'borrowed'
    GROUP BY period_key
    ORDER BY period_key
""", (start_date, end_date))
```

- [ ] **Step 3: 添加book_categories(bib_id)索引**

在 `database.py` 的 `ensure_indexes()` 函数中添加：

```python
cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_book_cat_bib_id
    ON book_categories(bib_id)
""")
```

- [ ] **Step 4: 验证后端导入**

Run: `cd library_data_analysis_fastapi && python -c "from app.routers.statistics import router; from app.database import ensure_indexes; print('OK')"`

---

### Task 2: 前端SWR缓存 + 错误/空状态 + 拆分loading

**Files:**
- Modify: `library_data_analysis_vue/src/api/index.ts`
- Modify: `library_data_analysis_vue/src/views/StatisticsView.vue`

- [ ] **Step 1: 添加stats路径SWR缓存配置**

在 `index.ts` 的 `PATH_TTL_CONFIG` 中添加：

```typescript
'/api/stats/': { staleTime: 5 * 60 * 1000, cacheTime: 30 * 60 * 1000 },
```

- [ ] **Step 2: 拆分loading状态**

将 StatisticsView.vue 中的单一 `loading` ref 拆分为5个独立loading：

```typescript
const loadingStates = reactive({
  frequency: false,
  descriptive: false,
  crosstab: false,
  clustering: false,
  forecast: false
})
const loading = computed(() => Object.values(loadingStates).some(v => v))
```

每个fetch函数使用对应的loading状态。

- [ ] **Step 3: 添加错误状态**

为每个Tab添加error ref：

```typescript
const errorStates = reactive({
  frequency: null as string | null,
  descriptive: null as string | null,
  crosstab: null as string | null,
  clustering: null as string | null,
  forecast: null as string | null
})
```

在catch中设置error，在template中展示错误提示。

- [ ] **Step 4: 添加空状态展示**

在template中，当数据为null且非loading且无error时，显示"暂无数据"提示。

- [ ] **Step 5: 修复硬编码中文**

将 `借${bin}次`、`次`、`本` 替换为i18n key：

```typescript
// 在 stats i18n 中添加:
borrowCountBin: '借{n}次',
timesUnit: '次',
booksUnit: '本',

// 使用:
t('stats.borrowCountBin', { n: bin })
t('stats.timesUnit')
t('stats.booksUnit')
```

---

### Task 3: 增加筛选功能

**Files:**
- Modify: `library_data_analysis_vue/src/views/StatisticsView.vue`
- Modify: `library_data_analysis_vue/src/views/StatisticsView.css`

- [ ] **Step 1: 添加年份筛选控件**

在频次分析Tab顶部添加年份选择器：

```html
<div class="filter-bar">
  <select v-model="selectedYear" class="filter-select" @change="fetchFrequency">
    <option v-for="yr in availableYears" :key="yr" :value="yr">{{ yr }}</option>
  </select>
</div>
```

```typescript
const selectedYear = ref(new Date().getFullYear())
const availableYears = computed(() => {
  const current = new Date().getFullYear()
  return Array.from({ length: 4 }, (_, i) => current - i)
})
```

- [ ] **Step 2: 为聚类和预测Tab添加年份筛选**

同样的年份选择器组件，绑定到各自的API参数。

- [ ] **Step 3: 为预测Tab添加快捷时段选择**

```html
<div class="quick-periods">
  <button v-for="p in quickPeriods" :key="p.days"
    :class="['quick-btn', { active: forecastDays === p.days }]"
    @click="forecastDays = p.days; fetchForecast()">
    {{ p.label }}
  </button>
</div>
```

```typescript
const quickPeriods = [
  { days: 7, label: t('stats.7days') },
  { days: 14, label: t('stats.14days') },
  { days: 30, label: t('stats.30days') }
]
```

- [ ] **Step 4: 添加筛选控件样式**

在 StatisticsView.css 中添加：

```css
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.filter-select {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-neutral-200);
  background: var(--chart-bg);
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
}

.quick-periods {
  display: flex;
  gap: var(--space-2);
}

.quick-btn {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-neutral-200);
  background: transparent;
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn.active {
  background: var(--data-borrow);
  color: white;
  border-color: var(--data-borrow);
}
```

---

### Task 4: 增加概览卡片

**Files:**
- Modify: `library_data_analysis_vue/src/views/StatisticsView.vue`
- Modify: `library_data_analysis_vue/src/views/StatisticsView.css`

- [ ] **Step 1: 为频次分析Tab添加概览卡片**

在频次分析Tab的图表上方，添加3个signal-card风格的概览卡片：

```typescript
const frequencyCards = computed(() => {
  if (!frequencyData.value) return []
  const d = frequencyData.value
  return [
    { label: t('stats.totalSamples'), value: formatNumber(d.total_count), color: 'var(--data-borrow)' },
    { label: t('stats.mean'), value: d.mean?.toFixed(1) || '-', color: 'var(--data-reader)' },
    { label: t('stats.median'), value: d.median?.toFixed(1) || '-', color: 'var(--data-return)' }
  ]
})
```

- [ ] **Step 2: 为描述统计Tab添加概览卡片**

展示关键统计指标：均值、标准差、中位数、样本数。

- [ ] **Step 3: 为聚类分析Tab添加概览卡片**

展示：总分析读者数、聚类数量、最大群体人数。

- [ ] **Step 4: 为预测Tab添加概览卡片**

展示：历史总计、历史日均、预测天数、预测趋势。

- [ ] **Step 5: 添加signal-grid样式**

复用 HistoricalAnalysisView.css 中的 signal-card 样式：

```css
.signal-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
  flex-shrink: 0;
  margin-bottom: var(--space-3);
}
```

---

### Task 5: 快照导出功能

**Files:**
- Modify: `library_data_analysis_fastapi/app/routers/statistics.py`
- Modify: `library_data_analysis_vue/src/api/statistics.ts`
- Modify: `library_data_analysis_vue/src/views/StatisticsView.vue`

- [ ] **Step 1: 后端添加快照存储端点**

在 statistics.py 中添加：

```python
@router.post("/snapshot")
async def save_snapshot(snapshot: dict):
    cache_key = f"stats:snapshot:{snapshot.get('id', '')}"
    cache.cache_set(cache_key, snapshot, 3600 * 24)  # 24小时TTL
    return {"status": "ok", "id": snapshot.get("id")}
```

- [ ] **Step 2: 前端API添加saveSnapshot方法**

在 statistics.ts 中添加：

```typescript
async saveSnapshot(data: Record<string, any>) {
  const id = `snapshot_${Date.now()}`
  return post('/api/stats/snapshot', { id, ...data })
}
```

- [ ] **Step 3: 在StatisticsView中添加快照按钮**

在每个Tab的ChartCard actions插槽中添加快照按钮：

```html
<button class="snapshot-btn" @click="saveCurrentSnapshot" :title="t('stats.saveSnapshot')">
  <svg><!-- camera icon --></svg>
</button>
```

```typescript
const saveCurrentSnapshot = async () => {
  const tabData = { tab: activeTab.value, data: getCurrentTabData(), timestamp: new Date().toISOString() }
  await statisticsApi.saveSnapshot(tabData)
  // 显示保存成功提示
}
```

---

### Task 6: i18n更新

**Files:**
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-CN/stats.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/en/stats.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-TW/stats.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/ja/stats.ts`

- [ ] **Step 1: 在4个语言文件中同步添加新key**

新增key列表：

| Key | zh-CN | en | zh-TW | ja |
|-----|-------|----|----|-------|
| `borrowCountBin` | 借{n}次 | Borrow {n} times | 借{n}次 | {n}回貸出 |
| `timesUnit` | 次 | times | 次 | 回 |
| `booksUnit` | 本 | books | 本 | 冊 |
| `7days` | 7天 | 7 Days | 7天 | 7日 |
| `14days` | 14天 | 14 Days | 14天 | 14日 |
| `30days` | 30天 | 30 Days | 30天 | 30日 |
| `saveSnapshot` | 保存快照 | Save Snapshot | 儲存快照 | スナップショット保存 |
| `snapshotSaved` | 快照已保存 | Snapshot Saved | 快照已儲存 | スナップショット保存済み |
| `totalSamples` | 总样本数 | Total Samples | 總樣本數 | 総サンプル数 |
| `noData` | 暂无数据 | No Data | 暫無數據 | データなし |
| `loadError` | 加载失败 | Load Failed | 載入失敗 | 読み込み失敗 |
| `retry` | 重试 | Retry | 重試 | 再試行 |
| `yearFilter` | 年份 | Year | 年份 | 年 |
| `forecastTrend` | 预测趋势 | Forecast Trend | 預測趨勢 | 予測トレンド |

---

### Task 7: 构建验证 + 重启

**Files:** 无新文件

- [ ] **Step 1: 前端构建验证**

Run: `cd library_data_analysis_vue && npm run build`
Expected: 构建成功，无错误

- [ ] **Step 2: 后端导入验证**

Run: `cd library_data_analysis_fastapi && python -c "from app.routers.statistics import router; print('OK')"`
Expected: OK

- [ ] **Step 3: 重启服务验证**

Run: `start.bat`
Expected: 前后端正常启动

- [ ] **Step 4: 功能验证**

访问统计分析页面，验证：
- 5个Tab正常切换
- 概览卡片正常显示
- 年份筛选正常工作
- 预测天数选择（7/14/30）正常工作
- 快照保存按钮可用
- 错误/空状态正常展示
