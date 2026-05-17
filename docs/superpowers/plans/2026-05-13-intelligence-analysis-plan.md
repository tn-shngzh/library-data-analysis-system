# 智能分析模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现关联分析和馆藏优化建议功能，包含力导向图和筛选列表

**Architecture:** 
- 前端：Vue 3 + D3.js 力导向图
- 后端：FastAPI 新增 intelligence 路由
- 数据：基于 circulations 表的读者借阅历史

**Tech Stack:** Vue 3, D3.js, FastAPI, PostgreSQL

---

## File Structure

### 后端文件
- Create: `library_data_analysis_fastapi/app/routers/intelligence.py` - 智能分析API路由

### 前端文件
- Create: `library_data_analysis_vue/src/views/IntelligenceView.vue` - 智能分析主页面
- Create: `library_data_analysis_vue/src/views/CorrelationChart.vue` - 力导向图组件
- Create: `library_data_analysis_vue/src/views/OptimizationList.vue` - 馆藏优化列表组件
- Modify: `library_data_analysis_vue/src/views/DashboardView.vue` - 添加导航项
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-CN/nav.ts` - 中文翻译
- Modify: `library_data_analysis_vue/src/i18n/locales/en/nav.ts` - 英文翻译
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-TW/nav.ts` - 繁体翻译
- Modify: `library_data_analysis_vue/src/i18n/locales/ja/nav.ts` - 日语翻译

---

## Implementation Tasks

### Task 1: 后端 - 关联分析API

**Files:**
- Create: `library_data_analysis_fastapi/app/routers/intelligence.py`
- Test: 使用 curl 测试 API

- [ ] **Step 1: 创建 intelligence.py 路由文件**

```python
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.database import run_sync_db
from app.cache import cache
from app.auth import get_current_user

router = APIRouter(prefix="/api/intelligence", tags=["智能分析"])
logger = logging.getLogger(__name__)
```

- [ ] **Step 2: 实现关联分析API (get_correlation)**

```python
@router.get("/correlation")
async def get_correlation(
    year_range: str = Query("all", description="时间范围: 1|2|all"),
    min_support: float = Query(0.05, description="最小支持度"),
    limit: int = Query(100, description="返回最大节点数"),
    current_user=Depends(get_current_user)
):
    """获取图书关联数据用于力导向图"""
    cache_key = f"intelligence:correlation:{year_range}:{min_support}:{limit}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached
    
    def _query(conn):
        with conn.cursor() as cur:
            # 构建时间范围
            if year_range == "all":
                time_condition = ""
                params = ()
            else:
                years = int(year_range) if year_range.isdigit() else 1
                start_date = (datetime.now() - timedelta(days=365 * years)).date()
                time_condition = "WHERE c.action_date >= %s"
                params = (int(start_date.strftime('%Y%m%d')),)
            
            # 关联分析 SQL: 找出同一读者借阅的所有书组合
            sql = f"""
                WITH reader_books AS (
                    SELECT borrower_id, bib_id, action_date
                    FROM circulations c
                    {time_condition}
                ),
                book_pairs AS (
                    SELECT DISTINCT rb1.bib_id as book1, rb2.bib_id as book2, COUNT(*) as co_count
                    FROM reader_books rb1
                    JOIN reader_books rb2 ON rb1.borrower_id = rb2.borrower_id 
                        AND rb1.bib_id < rb2.bib_id
                    GROUP BY rb1.bib_id, rb2.bib_id
                    HAVING COUNT(*) >= 5
                ),
                book_stats AS (
                    SELECT bib_id, COUNT(DISTINCT borrower_id) as reader_count
                    FROM reader_books
                    GROUP BY bib_id
                )
                SELECT 
                    bp.book1,
                    bc1.name as book1_name,
                    bc1.category as book1_category,
                    bp.book2,
                    bc2.name as book2_name,
                    bc2.category as book2_category,
                    bp.co_count,
                    bs1.reader_count as book1_readers,
                    bs2.reader_count as book2_readers,
                    CAST(bp.co_count AS FLOAT) / LEAST(bs1.reader_count, bs2.reader_count) as confidence
                FROM book_pairs bp
                JOIN book_categories bc1 ON bp.book1 = bc1.bib_id
                JOIN book_categories bc2 ON bp.book2 = bc2.bib_id
                JOIN book_stats bs1 ON bp.book1 = bs1.bib_id
                JOIN book_stats bs2 ON bp.book2 = bs2.bib_id
                ORDER BY bp.co_count DESC, confidence DESC
                LIMIT %s
            """
            params = params + (limit,)
            cur.execute(sql, params)
            rows = cur.fetchall()
            
            # 构建节点和边
            nodes_map = {}
            links = []
            
            for row in rows:
                book1_id, book1_name, book1_cat, book2_id, book2_name, book2_cat, co_count, readers1, readers2, confidence = row
                
                if book1_id not in nodes_map:
                    nodes_map[book1_id] = {
                        "id": book1_id,
                        "name": book1_name or f"图书{book1_id}",
                        "category": book1_cat,
                        "readers": readers1
                    }
                
                if book2_id not in nodes_map:
                    nodes_map[book2_id] = {
                        "id": book2_id,
                        "name": book2_name or f"图书{book2_id}",
                        "category": book2_cat,
                        "readers": readers2
                    }
                
                links.append({
                    "source": book1_id,
                    "target": book2_id,
                    "value": co_count,
                    "confidence": round(confidence * 100, 1)
                })
            
            return {
                "nodes": list(nodes_map.values()),
                "links": links,
                "total_pairs": len(links)
            }
    
    result = await run_sync_db(_query)
    cache.cache_set(cache_key, result, 3600)
    return result
```

- [ ] **Step 3: 在 __init__.py 注册路由**

```python
# library_data_analysis_fastapi/app/routers/__init__.py
from .intelligence import router as intelligence_router
```

- [ ] **Step 4: 在 main.py 挂载路由**

```python
# library_data_analysis_fastapi/app/main.py
from app.routers.intelligence import router as intelligence_router
app.include_router(intelligence_router)
```

- [ ] **Step 5: 测试API**

Run: `curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/intelligence/correlation?limit=50"`
Expected: 返回 {nodes: [...], links: [...], total_pairs: N}

---

### Task 2: 后端 - 馆藏优化API

**Files:**
- Modify: `library_data_analysis_fastapi/app/routers/intelligence.py`

- [ ] **Step 1: 实现馆藏优化API (get_collection_optimization)**

```python
@router.get("/collection-optimization")
async def get_collection_optimization(
    never_borrowed: bool = Query(True, description="包含从未被借"),
    low_freq_threshold: int = Query(5, description="低频阈值"),
    idle_months: int = Query(4, description="闲置月数"),
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(50, description="每页数量"),
    current_user=Depends(get_current_user)
):
    """获取馆藏优化建议"""
    cache_key = f"intelligence:optimization:{never_borrowed}:{low_freq_threshold}:{idle_months}:{category}:{page}:{page_size}"
    cached = cache.cache_get(cache_key)
    if cached is not None:
        return cached
    
    def _query(conn):
        with conn.cursor() as cur:
            idle_date = (datetime.now() - timedelta(days=idle_months * 30)).strftime('%Y%m%d')
            
            # 从未被借的书
            if never_borrowed:
                cur.execute("""
                    SELECT bc.bib_id, bc.name, bc.category, 
                           0 as borrow_count, NULL as last_borrow_date,
                           'never_borrowed' as issue_type
                    FROM book_categories bc
                    LEFT JOIN (
                        SELECT bib_id, MAX(action_date) as last_date
                        FROM circulations
                        GROUP BY bib_id
                    ) lc ON bc.bib_id = lc.bib_id
                    WHERE lc.bib_id IS NULL
                """)
                never_rows = cur.fetchall()
            else:
                never_rows = []
            
            # 低频借阅的书
            cur.execute("""
                SELECT bc.bib_id, bc.name, bc.category,
                       COALESCE(bc.borrow_count, 0) as borrow_count,
                       lc.last_date,
                       'low_frequency' as issue_type
                FROM book_categories bc
                LEFT JOIN (
                    SELECT bib_id, MAX(action_date) as last_date
                    FROM circulations
                    GROUP BY bib_id
                ) lc ON bc.bib_id = lc.bib_id
                WHERE COALESCE(bc.borrow_count, 0) < %s
                AND lc.bib_id IS NOT NULL
            """, (low_freq_threshold,))
            low_freq_rows = cur.fetchall()
            
            # 长期闲置的书
            cur.execute("""
                SELECT bc.bib_id, bc.name, bc.category,
                       COALESCE(bc.borrow_count, 0) as borrow_count,
                       lc.last_date,
                       'idle' as issue_type
                FROM book_categories bc
                JOIN (
                    SELECT bib_id, MAX(action_date) as last_date
                    FROM circulations
                    GROUP BY bib_id
                    HAVING MAX(action_date) < %s
                ) lc ON bc.bib_id = lc.bib_id
                WHERE COALESCE(bc.borrow_count, 0) >= %s
            """, (idle_date, low_freq_threshold))
            idle_rows = cur.fetchall()
            
            # 合并结果
            all_rows = never_rows + low_freq_rows + idle_rows
            
            # 分类筛选
            if category:
                all_rows = [r for r in all_rows if r[2] == category]
            
            # 格式化
            issues = []
            for row in all_rows:
                bib_id, name, cat, count, last_date, issue = row
                last_date_str = str(last_date) if last_date else None
                issues.append({
                    "bib_id": bib_id,
                    "name": name or f"图书{bib_id}",
                    "category": cat,
                    "borrow_count": count,
                    "last_borrow_date": last_date_str,
                    "issue_type": issue,
                    "issue_type_name": {"never_borrowed": "从未被借", "low_frequency": "低频借阅", "idle": "长期闲置"}.get(issue, issue)
                })
            
            # 排序
            issues.sort(key=lambda x: (
                {"never_borrowed": 0, "low_frequency": 1, "idle": 2}.get(x["issue_type"], 3),
                x["borrow_count"],
                x["last_borrow_date"] or ""
            ))
            
            total = len(issues)
            start = (page - 1) * page_size
            end = start + page_size
            paginated = issues[start:end]
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "list": paginated
            }
    
    result = await run_sync_db(_query)
    cache.cache_set(cache_key, result, 3600)
    return result
```

- [ ] **Step 2: 测试API**

Run: `curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/intelligence/collection-optimization?never_borrowed=true&low_freq_threshold=5&idle_months=4"`
Expected: 返回 {total: N, page: 1, list: [...]}

---

### Task 3: 前端 - 智能分析主页面

**Files:**
- Create: `library_data_analysis_vue/src/views/IntelligenceView.vue`

- [ ] **Step 1: 创建 IntelligenceView.vue**

```vue
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import CorrelationChart from './CorrelationChart.vue'
import OptimizationList from './OptimizationList.vue'

const { t } = useI18n()
const props = defineProps({
  allData: { type: Object, default: null }
})

const activeTab = ref('correlation')
const loading = ref(false)

const tabs = [
  { id: 'correlation', label: 'intelligence.correlation', icon: 'link' },
  { id: 'optimization', label: 'intelligence.optimization', icon: 'alert-triangle' }
]

const setActiveTab = (tabId) => {
  activeTab.value = tabId
}
</script>

<template>
  <div class="intelligence-view">
    <div class="page-header">
      <h1>{{ t('intelligence.title') }}</h1>
      <p>{{ t('intelligence.desc') }}</p>
    </div>

    <div class="tabs-container">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="setActiveTab(tab.id)"
      >
        {{ t(tab.label) }}
      </button>
    </div>

    <div class="tab-content">
      <CorrelationChart v-if="activeTab === 'correlation'" :all-data="allData" />
      <OptimizationList v-if="activeTab === 'optimization'" :all-data="allData" />
    </div>
  </div>
</template>

<style scoped>
.intelligence-view {
  max-width: 1400px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.page-header p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.tabs-container {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.tab-btn.active {
  background: #d97706;
  color: white;
}

.tab-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  min-height: 500px;
}
</style>
```

---

### Task 4: 前端 - 力导向图组件

**Files:**
- Create: `library_data_analysis_vue/src/views/CorrelationChart.vue`

- [ ] **Step 1: 创建 CorrelationChart.vue**

```vue
<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import * as d3 from 'd3'

const { t } = useI18n()
const props = defineProps({
  allData: { type: Object, default: null }
})

const chartContainer = ref(null)
const loading = ref(false)
const correlationData = ref(null)
const yearRange = ref('all')
const searchQuery = ref('')

const yearOptions = [
  { value: '1', label: 'intelligence.year1' },
  { value: '2', label: 'intelligence.year2' },
  { value: 'all', label: 'intelligence.all' }
]

const fetchCorrelationData = async () => {
  loading.value = true
  try {
    const response = await fetch(`/api/intelligence/correlation?year_range=${yearRange.value}&limit=150`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    correlationData.value = await response.json()
    await nextTick()
    renderForceChart()
  } catch (e) {
    console.error('获取关联数据失败', e)
  } finally {
    loading.value = false
  }
}

const renderForceChart = () => {
  if (!chartContainer.value || !correlationData.value) return
  
  const container = chartContainer.value
  d3.select(container).selectAll('*').remove()
  
  const width = container.clientWidth
  const height = 600
  
  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', [0, 0, width, height])
  
  const g = svg.append('g')
  
  const nodes = correlationData.value.nodes.map(n => ({...n}))
  const links = correlationData.value.links.map(l => ({
    source: l.source,
    target: l.target,
    value: l.value,
    confidence: l.confidence
  }))
  
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))
  
  const categoryColors = {
    '文学': '#6366f1',
    '科技': '#10b981',
    '历史': '#f59e0b',
    '艺术': '#ec4899',
    '哲学': '#8b5cf6',
    '其他': '#94a3b8'
  }
  
  const link = g.append('g')
    .attr('stroke', '#cbd5e1')
    .attr('stroke-opacity', 0.6)
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke-width', d => Math.sqrt(d.value / 10))
  
  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))
  
  node.append('circle')
    .attr('r', d => Math.sqrt(d.readers) * 2 + 8)
    .attr('fill', d => categoryColors[d.category] || categoryColors['其他'])
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')
    .on('click', (event, d) => showNodeDetail(d))
  
  node.append('text')
    .text(d => d.name.substring(0, 10) + (d.name.length > 10 ? '...' : ''))
    .attr('text-anchor', 'middle')
    .attr('dy', d => Math.sqrt(d.readers) * 2 + 20)
    .attr('font-size', '11px')
    .attr('fill', '#475569')
  
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
    
    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })
  
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }
  
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

const showNodeDetail = (node) => {
  alert(`${node.name}\n分类: ${node.category}\n借阅人数: ${node.readers}`)
}

const highlightNode = () => {
  if (!searchQuery.value) return
  const query = searchQuery.value.toLowerCase()
  d3.select(chartContainer.value)
    .selectAll('circle')
    .attr('stroke', d => d.name.toLowerCase().includes(query) ? '#f59e0b' : '#fff')
    .attr('stroke-width', d => d.name.toLowerCase().includes(query) ? 4 : 2)
}

watch(yearRange, fetchCorrelationData)
watch(searchQuery, highlightNode)
onMounted(fetchCorrelationData)
</script>

<template>
  <div class="correlation-chart">
    <div class="chart-controls">
      <div class="control-group">
        <label>{{ t('intelligence.timeRange') }}</label>
        <select v-model="yearRange">
          <option v-for="opt in yearOptions" :key="opt.value" :value="opt.value">
            {{ t(opt.label) }}
          </option>
        </select>
      </div>
      <div class="control-group">
        <label>{{ t('intelligence.search') }}</label>
        <input v-model="searchQuery" type="text" :placeholder="t('intelligence.searchPlaceholder')" />
      </div>
      <div class="stats-info" v-if="correlationData">
        <span>{{ t('intelligence.nodes') }}: {{ correlationData.nodes.length }}</span>
        <span>{{ t('intelligence.links') }}: {{ correlationData.links.length }}</span>
      </div>
    </div>
    
    <div ref="chartContainer" class="chart-container"></div>
    
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<style scoped>
.correlation-chart {
  position: relative;
}

.chart-controls {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-group label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.control-group select,
.control-group input {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.stats-info {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-left: auto;
  color: #64748b;
  font-size: 13px;
}

.chart-container {
  width: 100%;
  height: 600px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #d97706;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
```

---

### Task 5: 前端 - 馆藏优化列表组件

**Files:**
- Create: `library_data_analysis_vue/src/views/OptimizationList.vue`

- [ ] **Step 1: 创建 OptimizationList.vue**

```vue
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  allData: { type: Object, default: null }
})

const loading = ref(false)
const optimizationData = ref(null)
const filters = ref({
  issueType: 'all',
  category: '',
  sortBy: 'issue'
})
const pagination = ref({ page: 1, pageSize: 50 })

const issueTypes = [
  { value: 'all', label: 'intelligence.allTypes' },
  { value: 'never_borrowed', label: 'intelligence.neverBorrowed' },
  { value: 'low_frequency', label: 'intelligence.lowFrequency' },
  { value: 'idle', label: 'intelligence.idle' }
]

const fetchOptimizationData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      never_borrowed: 'true',
      low_freq_threshold: '5',
      idle_months: '4',
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    })
    if (filters.value.category) {
      params.append('category', filters.value.category)
    }
    
    const response = await fetch(`/api/intelligence/collection-optimization?${params}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
    optimizationData.value = await response.json()
  } catch (e) {
    console.error('获取优化数据失败', e)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
}

const changePage = (page) => {
  pagination.value.page = page
  fetchOptimizationData()
}

watch([filters, pagination.page], fetchOptimizationData)
onMounted(fetchOptimizationData)
</script>

<template>
  <div class="optimization-list">
    <div class="filter-bar">
      <div class="filter-group">
        <label>{{ t('intelligence.issueType') }}</label>
        <select v-model="filters.issueType">
          <option v-for="opt in issueTypes" :key="opt.value" :value="opt.value">
            {{ t(opt.label) }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label>{{ t('intelligence.category') }}</label>
        <select v-model="filters.category">
          <option value="">全部分类</option>
          <option value="文学">文学</option>
          <option value="科技">科技</option>
          <option value="历史">历史</option>
          <option value="艺术">艺术</option>
          <option value="哲学">哲学</option>
        </select>
      </div>
      <div class="filter-group">
        <label>{{ t('intelligence.sortBy') }}</label>
        <select v-model="filters.sortBy">
          <option value="issue">{{ t('intelligence.sortByIssue') }}</option>
          <option value="count">{{ t('intelligence.sortByCount') }}</option>
          <option value="date">{{ t('intelligence.sortByDate') }}</option>
        </select>
      </div>
      <div class="filter-summary" v-if="optimizationData">
        {{ t('intelligence.total') }}: {{ optimizationData.total }}
      </div>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>{{ t('intelligence.bookName') }}</th>
          <th>{{ t('intelligence.category') }}</th>
          <th>{{ t('intelligence.issueType') }}</th>
          <th>{{ t('intelligence.lastBorrow') }}</th>
          <th>{{ t('intelligence.borrowCount') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in optimizationData?.list" :key="item.bib_id">
          <td>{{ item.name }}</td>
          <td>{{ item.category }}</td>
          <td>
            <span class="issue-badge" :class="item.issue_type">
              {{ item.issue_type_name }}
            </span>
          </td>
          <td>{{ formatDate(item.last_borrow_date) }}</td>
          <td>{{ item.borrow_count }}</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination" v-if="optimizationData">
      <button 
        :disabled="pagination.page === 1"
        @click="changePage(pagination.page - 1)"
      >
        {{ t('common.prev') }}
      </button>
      <span>{{ pagination.page }} / {{ Math.ceil(optimizationData.total / pagination.pageSize) }}</span>
      <button 
        :disabled="pagination.page >= Math.ceil(optimizationData.total / pagination.pageSize)"
        @click="changePage(pagination.page + 1)"
      >
        {{ t('common.next') }}
      </button>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
    </div>
  </div>
</template>

<style scoped>
.optimization-list {
  position: relative;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 12px;
  color: #64748b;
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.filter-summary {
  margin-left: auto;
  color: #64748b;
  font-size: 14px;
  align-self: flex-end;
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
  color: #64748b;
  text-transform: uppercase;
  border-bottom: 2px solid #e2e8f0;
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: #475569;
  border-bottom: 1px solid #f1f5f9;
}

.issue-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.issue-badge.never_borrowed {
  background: #fef2f2;
  color: #ef4444;
}

.issue-badge.low_frequency {
  background: #fffbeb;
  color: #f59e0b;
}

.issue-badge.idle {
  background: #f0fdf4;
  color: #10b981;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #d97706;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
```

---

### Task 6: 前端 - 导航和国际化

**Files:**
- Modify: `library_data_analysis_vue/src/views/DashboardView.vue`
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-CN/nav.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/en/nav.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/zh-TW/nav.ts`
- Modify: `library_data_analysis_vue/src/i18n/locales/ja/nav.ts`

- [ ] **Step 1: 添加导航项到 DashboardView.vue**

在 navItems 中添加:
```javascript
{ id: 'intelligence', i18nKey: 'nav.intelligence', icon: 'brain', pinned: true, closable: false, loaded: false }
```

在 tab-content 中添加:
```vue
<div v-else-if="activeNavId === 'intelligence'" key="intelligence" class="tab-panel">
  <IntelligenceView :all-data="store" />
</div>
```

- [ ] **Step 2: 添加国际化翻译**

zh-CN/nav.ts:
```typescript
export default {
  // ... existing
  intelligence: '智能分析',
}
```

en/nav.ts:
```typescript
export default {
  // ... existing
  intelligence: 'Intelligence',
}
```

zh-TW/nav.ts:
```typescript
export default {
  // ... existing
  intelligence: '智能分析',
}
```

ja/nav.ts:
```typescript
export default {
  // ... existing
  intelligence: 'インテリジェンス',
}
```

---

### Task 7: 添加智能分析国际化文本

**Files:**
- Create: `library_data_analysis_vue/src/i18n/locales/zh-CN/intelligence.ts`
- Create: `library_data_analysis_vue/src/i18n/locales/en/intelligence.ts`
- Create: `library_data_analysis_vue/src/i18n/locales/zh-TW/intelligence.ts`
- Create: `library_data_analysis_vue/src/i18n/locales/ja/intelligence.ts`

- [ ] **Step 1: 创建中文翻译文件**

```typescript
export default {
  title: '智能分析',
  desc: '基于千万级借阅数据的关联分析和馆藏优化建议',
  correlation: '关联分析',
  optimization: '馆藏优化',
  timeRange: '时间范围',
  year1: '近1年',
  year2: '近2年',
  all: '全部',
  search: '搜索',
  searchPlaceholder: '输入书名搜索...',
  nodes: '图书节点',
  links: '关联对数',
  issueType: '问题类型',
  category: '分类',
  sortBy: '排序',
  sortByIssue: '按问题类型',
  sortByCount: '按借阅次数',
  sortByDate: '按最后借阅',
  total: '问题图书总数',
  bookName: '图书名称',
  lastBorrow: '最后借阅',
  borrowCount: '借阅次数',
  allTypes: '全部类型',
  neverBorrowed: '从未被借',
  lowFrequency: '低频借阅',
  idle: '长期闲置'
}
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| Task 1 | 后端关联分析API | intelligence.py |
| Task 2 | 后场馆藏优化API | intelligence.py |
| Task 3 | 智能分析主页面 | IntelligenceView.vue |
| Task 4 | 力导向图组件 | CorrelationChart.vue |
| Task 5 | 馆藏优化列表组件 | OptimizationList.vue |
| Task 6 | 导航和国际化 | DashboardView.vue, nav.ts |
| Task 7 | 智能分析翻译文件 | intelligence.ts (4 languages) |