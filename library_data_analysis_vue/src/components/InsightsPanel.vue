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

const severityConfig = {
  success: {
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    iconBg: 'rgba(255,255,255,0.2)'
  },
  warning: {
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    iconBg: 'rgba(255,255,255,0.2)'
  },
  info: {
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    iconBg: 'rgba(255,255,255,0.2)'
  }
}

const typeGradients = {
  category: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  time: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  warning: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  trend: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
}

const getCardStyle = (insight) => {
  const gradient = typeGradients[insight.type] || severityConfig[insight.severity]?.gradient || severityConfig.info.gradient
  return {
    background: gradient,
    '--delay': (props.insights.indexOf(insight) * 0.08) + 's'
  }
}
</script>

<template>
  <div class="insights-panel">
    <div class="insights-header">
      <span class="insights-icon">✨</span>
      <span class="insights-title">{{ t('insights.title', '智能洞察') }}</span>
    </div>
    <div class="insights-grid">
      <div
        v-for="insight in insights"
        :key="insight.id"
        class="insight-card"
        :style="getCardStyle(insight)"
      >
        <div class="insight-icon-wrapper">
          <span class="insight-emoji">{{ insight.icon }}</span>
        </div>
        <div class="insight-content">
          <div class="insight-title">{{ insight.title }}</div>
          <div class="insight-main">{{ insight.main }}</div>
          <div class="insight-reason">{{ insight.reason }}</div>
        </div>
        <div class="insight-trend" :class="insight.trend">
          <span v-if="insight.trend === 'up'">↑</span>
          <span v-else-if="insight.trend === 'down'">↓</span>
          <span v-else>→</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.insights-panel {
  background: var(--color-bg-primary, #fff);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.insights-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.insights-icon {
  font-size: 20px;
}

.insights-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary, #1e293b);
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.insight-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px;
  border-radius: 14px;
  color: white;
  animation: fadeInInsight 0.5s ease both;
  animation-delay: var(--delay);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
}

.insight-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s;
}

.insight-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,0.15);
}

.insight-card:hover::before {
  opacity: 1;
}

@keyframes fadeInInsight {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.insight-icon-wrapper {
  width: 44px;
  height: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(4px);
}

.insight-emoji {
  font-size: 22px;
  line-height: 1;
}

.insight-content {
  flex: 1;
  min-width: 0;
}

.insight-title {
  font-size: 13px;
  font-weight: 600;
  opacity: 0.9;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.insight-main {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  line-height: 1.3;
}

.insight-reason {
  font-size: 12px;
  opacity: 0.85;
  line-height: 1.4;
}

.insight-trend {
  font-size: 20px;
  font-weight: 700;
  opacity: 0.9;
  align-self: center;
}

.insight-trend.up {
  color: #90EE90;
}

.insight-trend.down {
  color: #FFB6C1;
}

@media (max-width: 768px) {
  .insights-grid {
    grid-template-columns: 1fr;
  }
  
  .insights-panel {
    padding: 16px;
  }
}
</style>
