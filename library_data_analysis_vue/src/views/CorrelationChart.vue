<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import * as d3 from 'd3'
import { intelligenceApi, type CorrelationData } from '@/api/intelligence'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(false)
const chartContainer = ref<HTMLDivElement | null>(null)
const searchQuery = ref('')
const stats = ref({ nodes: 0, links: 0 })

const yearRangeOptions = [
  { value: '1', label: t('intelligence.year1') },
  { value: '2', label: t('intelligence.year2') },
  { value: 'all', label: t('intelligence.all') }
]

const selectedYearRange = ref('2')
const correlationData = ref<CorrelationData | null>(null)

const categoryColors: Record<string, string> = {
  '文学': '#6366f1',
  '科技': '#10b981',
  '历史': '#f59e0b',
  '艺术': '#ec4899',
  '哲学': '#8b5cf6',
  '其他': '#94a3b8'
}

const fetchCorrelationData = async () => {
  loading.value = true
  try {
    const data = await intelligenceApi.getCorrelation(selectedYearRange.value, 0.05, 150)
    correlationData.value = data
    stats.value = {
      nodes: data.nodes?.length || 0,
      links: data.links?.length || 0
    }
    renderChart()
  } catch (error) {
    console.error('Failed to fetch correlation data:', error)
  } finally {
    loading.value = false
  }
}

const getCategoryColor = (category: string): string => {
  return categoryColors[category] || categoryColors['其他']
}

const getNodeRadius = (readers: number): number => {
  const minRadius = 8
  const maxRadius = 30
  const maxReaders = 100
  return Math.min(maxRadius, Math.max(minRadius, (readers / maxReaders) * maxRadius + minRadius))
}

const getLinkWidth = (value: number): number => {
  const minWidth = 1
  const maxWidth = 6
  const maxValue = 50
  return Math.min(maxWidth, Math.max(minWidth, (value / maxValue) * maxWidth + minWidth))
}

let simulation: d3.Simulation<any, any> | null = null
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let zoom: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null

const renderChart = () => {
  if (!chartContainer.value || !correlationData.value) return

  chartContainer.value.innerHTML = ''

  const width = chartContainer.value.clientWidth
  const height = 350

  svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const g = svg.append('g')

  zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom)

  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '-0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .append('path')
    .attr('d', 'M 0,-5 L 10,0 L 0,5')
    .attr('fill', '#cbd5e1')

  const nodes = correlationData.value.nodes.map(d => ({ ...d }))
  const links = correlationData.value.links.map(d => ({ ...d }))

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(40))

  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .enter()
    .append('line')
    .attr('stroke', '#cbd5e1')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', (d: any) => getLinkWidth(d.value))

  const node = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'node')
    .call(d3.drag<any, any>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  node.append('circle')
    .attr('r', (d: any) => getNodeRadius(d.readers))
    .attr('fill', (d: any) => getCategoryColor(d.category))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')

  node.append('text')
    .attr('dx', (d: any) => getNodeRadius(d.readers) + 4)
    .attr('dy', 4)
    .attr('font-size', '11px')
    .attr('fill', '#475569')
    .text((d: any) => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name)

  node.select('circle')
    .on('click', (event, d: any) => {
      showNodeDetail(d)
    })

  node.select('circle')
    .on('mouseover', function() {
      d3.select(this)
        .attr('stroke', '#3b82f6')
        .attr('stroke-width', 3)
    })
    .on('mouseout', function() {
      d3.select(this)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
    })

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })

  function dragstarted(event: any, d: any) {
    if (!event.active) simulation?.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  function dragged(event: any, d: any) {
    d.fx = event.x
    d.fy = event.y
  }

  function dragended(event: any, d: any) {
    if (!event.active) simulation?.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

const showNodeDetail = (node: any) => {
  const message = `${t('intelligence.bookName')}: ${node.name}\n${t('intelligence.category')}: ${node.category}\n${t('intelligence.readers')}: ${node.readers}`
  alert(message)
}

const highlightSearch = () => {
  if (!svg || !correlationData.value) return

  const query = searchQuery.value.toLowerCase().trim()
  if (!query) {
    svg.selectAll('.node circle')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
    svg.selectAll('.node text')
      .attr('font-weight', 'normal')
      .attr('fill', '#475569')
    return
  }

  svg.selectAll('.node').each(function(this: any, d: any) {
    const nodeData = d as any
    const isMatch = nodeData.name.toLowerCase().includes(query)

    d3.select(this).select('circle')
      .attr('stroke', isMatch ? '#ef4444' : '#fff')
      .attr('stroke-width', isMatch ? 4 : 2)

    d3.select(this).select('text')
      .attr('font-weight', isMatch ? 'bold' : 'normal')
      .attr('fill', isMatch ? '#ef4444' : '#475569')
  })
}

watch(searchQuery, () => {
  highlightSearch()
})

watch(selectedYearRange, () => {
  fetchCorrelationData()
})

onMounted(() => {
  fetchCorrelationData()
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
})
</script>

<template>
  <div class="correlation-chart">
    <div class="control-panel">
      <div class="control-group">
        <label class="control-label">{{ t('intelligence.timeRange') }}</label>
        <div class="button-group">
          <button
            v-for="option in yearRangeOptions"
            :key="option.value"
            class="range-btn"
            :class="{ active: selectedYearRange === option.value }"
            @click="selectedYearRange = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div class="control-group">
        <label class="control-label">{{ t('intelligence.search') }}</label>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          :placeholder="t('intelligence.searchPlaceholder')"
        />
      </div>

      <div class="stats-info">
        <div class="stat-item">
          <span class="stat-label">{{ t('intelligence.nodes') }}:</span>
          <span class="stat-value">{{ stats.nodes }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">{{ t('intelligence.links') }}:</span>
          <span class="stat-value">{{ stats.links }}</span>
        </div>
      </div>
    </div>

    <LoadingSpinner :loading="loading">
      <div ref="chartContainer" class="chart-container"></div>
    </LoadingSpinner>

    <div class="legend">
      <div v-for="(color, category) in categoryColors" :key="category" class="legend-item">
        <span class="legend-color" :style="{ backgroundColor: color }"></span>
        <span class="legend-label">{{ category }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.correlation-chart {
  width: 100%;
}

.control-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding: 16px 20px;
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 16px;
  align-items: flex-end;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.button-group {
  display: flex;
  gap: 4px;
}

.range-btn {
  padding: 8px 16px;
  border: 1px solid #e2e8f0;
  background: #fff;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.range-btn:hover:not(.active) {
  border-color: #3b82f6;
  color: #3b82f6;
}

.range-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  width: 200px;
  background: #fff;
  color: #1e293b;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.stats-info {
  display: flex;
  gap: 20px;
  margin-left: auto;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.chart-container {
  width: 100%;
  height: 350px;
  background: #f8fafc;
  border-radius: 10px;
  overflow: hidden;
}

.chart-container :deep(svg) {
  display: block;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 10px;
  margin-top: 16px;
  border: 1px solid #f1f5f9;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-label {
  font-size: 13px;
  color: #475569;
}
</style>