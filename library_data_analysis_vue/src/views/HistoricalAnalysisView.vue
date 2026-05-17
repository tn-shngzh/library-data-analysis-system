<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatNumber } from '@/utils/format'
import ChartCard from '@/components/ChartCard.vue'
import { BarChart, LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import { use } from 'echarts/core'
import VChart from 'vue-echarts'

use([BarChart, LineChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent])

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    required: true
  }
})

const stats = computed(() => props.allData?.overview?.historicalStats)
const detail = computed(() => props.allData?.overview?.historicalDetail)

const yearlyTrendStats = computed(() => {
  const h = stats.value
  if (!h || h.data_years === 0) return []
  const trend = h.yearly_trend || []
  const latestYear = trend.length > 0 ? trend[trend.length - 1] : null
  const prevYear = trend.length > 1 ? trend[trend.length - 2] : null
  const yoyGrowth = (latestYear && prevYear && prevYear.total > 0)
    ? ((latestYear.total - prevYear.total) / prevYear.total * 100).toFixed(1)
    : null
  return [
    { label: t('overview.histDataSpan'), value: h.data_years + t('overview.histYearSuffix') },
    { label: t('overview.histTotalCirc'), value: formatNumber(h.total_circulations) },
    { label: t('overview.histYoYGrowth'), value: yoyGrowth ? (yoyGrowth >= 0 ? '+' : '') + yoyGrowth + '%' : '-' }
  ]
})
const yearlyCompareStats = computed(() => {
  const h = stats.value
  if (!h || h.data_years === 0) return []
  const trend = h.yearly_trend || []
  const avgYearlyReaders = trend.length > 0
    ? Math.round(trend.reduce((s, y) => s + y.active_readers, 0) / trend.length)
    : 0
  const neverBorrowedPct = h.total_distinct_books > 0
    ? (h.never_borrowed_books / h.total_distinct_books * 100).toFixed(1)
    : '0'
  return [
    { label: t('overview.histActiveReaders'), value: formatNumber(h.total_active_readers) },
    { label: t('overview.histBookStats'), value: formatNumber(h.total_distinct_books) }
  ]
})
const monthlyDetailStats = computed(() => {
  const h = stats.value
  if (!h || h.data_years === 0) return []
  return [
    { label: t('overview.histPeakInfo'), value: h.peak_year_month }
  ]
})

const yearlyBarOption = computed(() => {
  const h = stats.value
  if (!h || !h.yearly_trend || h.yearly_trend.length === 0) return {}
  const trend = h.yearly_trend
  const yoyValues = trend.map((item, idx) => {
    if (idx === 0) return null
    const prev = trend[idx - 1]
    return prev.total > 0 ? +((item.total - prev.total) / prev.total * 100).toFixed(1) : 0
  })
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const idx = params[0].dataIndex
        const item = trend[idx]
        const yoyVal = yoyValues[idx]
        let html = `<b>${item.year}</b><br/>${t('overview.histBorrows')}: ${formatNumber(item.cko_count)}<br/>${t('overview.histReturns')}: ${formatNumber(item.cki_count)}<br/>${t('overview.histActiveReaders')}: ${formatNumber(item.active_readers)}<br/>${t('overview.histTotalCirc')}: ${formatNumber(item.total)}`
        if (yoyVal != null) {
          html += `<br/>${t('overview.yoy')}: ${yoyVal >= 0 ? '+' : ''}${yoyVal}%`
        }
        return html
      }
    },
    legend: {
      data: [t('overview.histBorrows'), t('overview.histReturns'), t('overview.yoy')],
      bottom: 0,
      textStyle: { fontSize: 11 }
    },
    grid: { left: 55, right: 55, bottom: 30, top: 24, containLabel: false },
    xAxis: {
      type: 'category',
      data: trend.map(i => i.year),
      axisLabel: { fontSize: 11 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: [
      {
        type: 'value',
        axisLabel: { fontSize: 10 },
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }
      },
      {
        type: 'value',
        position: 'right',
        axisLabel: { fontSize: 10, formatter: '{value}%' },
        splitLine: { show: false },
        scale: true
      }
    ],
    series: [
      {
        name: t('overview.histBorrows'),
        type: 'bar',
        stack: 'circ',
        data: trend.map(i => i.cko_count),
        itemStyle: { color: '#F5A623' },
        barWidth: '36%'
      },
      {
        name: t('overview.histReturns'),
        type: 'bar',
        stack: 'circ',
        data: trend.map(i => i.cki_count),
        itemStyle: { color: '#7ED321', borderRadius: [4, 4, 0, 0] },
        barWidth: '36%'
      },
      {
        name: t('overview.yoy'),
        type: 'line',
        yAxisIndex: 1,
        data: yoyValues.map((val) => ({
          value: val,
          itemStyle: { color: val == null ? '#4A90E2' : val >= 0 ? '#10b981' : '#ef4444' }
        })),
        symbol: 'circle',
        symbolSize: 10,
        lineStyle: { width: 3, color: '#4A90E2' },
        itemStyle: { borderWidth: 2, borderColor: '#fff' },
        label: {
          show: true,
          position: 'top',
          formatter: (p) => p.value == null ? '' : (p.value >= 0 ? '+' : '') + p.value + '%',
          fontSize: 12,
          fontWeight: 'bold',
          color: (p) => {
            const val = yoyValues[p.dataIndex]
            return val == null ? 'transparent' : val >= 0 ? '#10b981' : '#ef4444'
          },
          distance: 8
        },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#94a3b8', type: 'dashed', width: 1 },
          data: [{ yAxis: 0 }],
          label: { show: false }
        }
      }
    ]
  }
})

const yearlyRadarOption = computed(() => {
  const h = stats.value
  if (!h || !h.yearly_trend || h.yearly_trend.length < 2) return {}
  const trend = h.yearly_trend
  const avgCko = trend.reduce((s, i) => s + i.cko_count, 0) / trend.length
  const avgCki = trend.reduce((s, i) => s + i.cki_count, 0) / trend.length
  const avgReaders = trend.reduce((s, i) => s + i.active_readers, 0) / trend.length
  const avgTotal = trend.reduce((s, i) => s + i.total, 0) / trend.length
  const devData = trend.map(item => ({
    year: item.year,
    ckoDev: avgCko > 0 ? +((item.cko_count - avgCko) / avgCko * 100).toFixed(1) : 0,
    ckiDev: avgCki > 0 ? +((item.cki_count - avgCki) / avgCki * 100).toFixed(1) : 0,
    readersDev: avgReaders > 0 ? +((item.active_readers - avgReaders) / avgReaders * 100).toFixed(1) : 0,
    totalDev: avgTotal > 0 ? +((item.total - avgTotal) / avgTotal * 100).toFixed(1) : 0
  }))
  const allDev = devData.flatMap(d => [d.ckoDev, d.ckiDev, d.readersDev, d.totalDev])
  const maxAbs = Math.max(Math.abs(Math.min(...allDev)), Math.abs(Math.max(...allDev)), 5)
  const bound = Math.ceil(maxAbs / 5) * 5 + 5
  const indicator = [
    { name: t('overview.histBorrows'), max: bound, min: -bound },
    { name: t('overview.histReturns'), max: bound, min: -bound },
    { name: t('overview.histActiveReaders'), max: bound, min: -bound },
    { name: t('overview.histTotalCirc'), max: bound, min: -bound }
  ]
  const colors = ['#F5A623', '#4A90E2', '#7ED321', '#BD10E0']
  const seriesData = devData.map((item, idx) => ({
    value: [item.ckoDev, item.ckiDev, item.readersDev, item.totalDev],
    name: item.year + '',
    itemStyle: { color: colors[idx % colors.length] },
    areaStyle: { opacity: 0.2 },
    lineStyle: { width: 3 },
    symbol: 'circle',
    symbolSize: 7
  }))
  return {
    tooltip: {
      formatter: (params) => {
        const dd = devData.find(i => i.year + '' === params.name)
        if (!dd) return params.name
        const fmt = (v) => (v >= 0 ? '+' : '') + v + '%'
        const tag = (v) => v >= 0 ? ' ▲' : ' ▼'
        return `<b>${params.name} (${t('overview.histVsAvg')})</b><br/>${t('overview.histBorrows')}: ${fmt(dd.ckoDev)}${tag(dd.ckoDev)}<br/>${t('overview.histReturns')}: ${fmt(dd.ckiDev)}${tag(dd.ckiDev)}<br/>${t('overview.histActiveReaders')}: ${fmt(dd.readersDev)}${tag(dd.readersDev)}<br/>${t('overview.histTotalCirc')}: ${fmt(dd.totalDev)}${tag(dd.totalDev)}`
      }
    },
    legend: {
      data: devData.map(i => i.year + ''),
      bottom: 0,
      textStyle: { fontSize: 11 }
    },
    radar: {
      indicator,
      shape: 'polygon',
      radius: '62%',
      splitNumber: 4,
      axisName: { fontSize: 10 },
      splitArea: { areaStyle: { color: ['rgba(100,100,100,0.02)', 'rgba(100,100,100,0.05)'] } },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    series: [{ type: 'radar', data: seriesData }]
  }
})

const monthlyLineOption = computed(() => {
  const d = detail.value
  if (!d || d.length === 0) return {}
  const months = d.map(i => {
    const m = i.month.toString()
    return m.substring(0, 4) + '/' + m.substring(4, 6)
  })
  return {
    tooltip: { trigger: 'axis' },
    legend: {
      data: [t('overview.histBorrows'), t('overview.histReturns'), t('overview.histActiveReaders')],
      bottom: 0,
      textStyle: { fontSize: 11 }
    },
    grid: { left: 50, right: 50, bottom: 30, top: 12, containLabel: false },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { fontSize: 10, rotate: 45 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: [
      {
        type: 'value',
        position: 'left',
        axisLabel: { fontSize: 10 },
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }
      },
      {
        type: 'value',
        position: 'right',
        axisLabel: { fontSize: 10 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: t('overview.histBorrows'),
        type: 'line',
        data: d.map(i => i.cko_count),
        yAxisIndex: 0,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3,
        itemStyle: { color: '#F5A623' },
        lineStyle: { width: 2 }
      },
      {
        name: t('overview.histReturns'),
        type: 'line',
        data: d.map(i => i.cki_count),
        yAxisIndex: 0,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3,
        itemStyle: { color: '#7ED321' },
        lineStyle: { width: 2 }
      },
      {
        name: t('overview.histActiveReaders'),
        type: 'line',
        data: d.map(i => i.active_readers),
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3,
        itemStyle: { color: '#50E3C2' },
        lineStyle: { width: 2 }
      }
    ]
  }
})
</script>

<template>
  <div class="hist-container">
    <div v-if="stats?.yearly_trend?.length" class="hist-charts-row">
      <div class="hist-chart-left">
        <ChartCard :title="t('overview.histYearlyTrend')" color="var(--data-borrow)" :stats="yearlyTrendStats">
          <v-chart class="hist-chart" :option="yearlyBarOption" autoresize />
        </ChartCard>
      </div>
      <div class="hist-chart-right">
        <ChartCard :title="t('overview.histYearlyCompare')" color="var(--data-reader)" :stats="yearlyCompareStats">
          <v-chart class="hist-chart" :option="yearlyRadarOption" autoresize />
        </ChartCard>
      </div>
    </div>

    <div v-if="detail?.length" class="hist-monthly-row">
      <ChartCard :title="t('overview.histMonthlyDetail')" color="var(--data-return)" :stats="monthlyDetailStats">
        <v-chart class="hist-chart-full" :option="monthlyLineOption" autoresize />
      </ChartCard>
    </div>
  </div>
</template>

<style scoped src="./HistoricalAnalysisView.css"></style>
