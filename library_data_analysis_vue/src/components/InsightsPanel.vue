<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  insights: {
    type: Array,
    default: () => []
  }
})

const severityColors = {
  success: 'var(--chart-secondary, #10b981)',
  warning: 'var(--chart-accent, #f59e0b)',
  info: 'var(--chart-primary, #3b82f6)'
}

const typeIcons = {
  trend: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
  anomaly: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  recommendation: '<line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>',
  info: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'
}

const getSeverityColor = (severity) => severityColors[severity] || severityColors.info
const getTypeIcon = (type) => typeIcons[type] || typeIcons.info
</script>

<template>
  <div class="insights-panel">
    <div class="insights-header">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="insights-icon">
        <line x1="9" y1="18" x2="15" y2="18"/>
        <line x1="10" y1="22" x2="14" y2="22"/>
        <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
      </svg>
      <span class="insights-title">{{ t('insights.title') }}</span>
    </div>
    <div class="insights-list">
      <div v-for="(insight, index) in insights" :key="insight.id" class="insight-card" :style="{ '--accent': getSeverityColor(insight.severity), '--delay': (index * 0.08) + 's' }">
        <div class="insight-icon-wrapper" :style="{ color: getSeverityColor(insight.severity) }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="getTypeIcon(insight.type)"></svg>
        </div>
        <div class="insight-content">
          <div class="insight-title-row">
            <span class="insight-name">{{ insight.title }}</span>
            <span class="insight-badge" :class="insight.severity">{{ insight.severity }}</span>
          </div>
          <div class="insight-desc">{{ insight.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.insights-panel { background: var(--color-bg-primary, #fff); border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.insights-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.insights-icon { width: 22px; height: 22px; color: var(--chart-accent, #f59e0b); }
.insights-title { font-size: 16px; font-weight: 600; color: var(--color-text-primary, #1e293b); }
.insights-list { display: flex; flex-direction: column; gap: 10px; }
.insight-card { display: flex; gap: 12px; padding: 14px; border-radius: 10px; border-left: 3px solid var(--accent); background: var(--color-bg-secondary, #f8fafc); animation: fadeInInsight 0.4s ease both; animation-delay: var(--delay); transition: transform 0.15s; }
.insight-card:hover { transform: translateX(4px); }
@keyframes fadeInInsight { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.insight-icon-wrapper { width: 36px; height: 36px; min-width: 36px; display: flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(59,130,246,0.08); }
.insight-icon-wrapper svg { width: 18px; height: 18px; }
.insight-content { flex: 1; min-width: 0; }
.insight-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.insight-name { font-size: 14px; font-weight: 600; color: var(--color-text-primary, #1e293b); }
.insight-badge { font-size: 10px; font-weight: 600; padding: 1px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.insight-badge.success { background: rgba(16,185,129,0.12); color: var(--chart-secondary, #10b981); }
.insight-badge.warning { background: rgba(245,158,11,0.12); color: var(--chart-accent, #f59e0b); }
.insight-badge.info { background: rgba(59,130,246,0.12); color: var(--chart-primary, #3b82f6); }
.insight-desc { font-size: 13px; color: var(--color-text-secondary, #64748b); line-height: 1.5; }
</style>
